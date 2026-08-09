#!/usr/bin/env python3
"""
Continuously watches an image directory and creates web-optimized variants.

The script is intentionally idempotent:
- Existing categories in images.config.json are preserved.
- New images get category="".
- Missing generated variants are recreated.
- Deleted originals are removed from generated directories and the config.
- images.config.json is written atomically to avoid partially-written files.

Supported input formats depend on Pillow. JPG/JPEG, PNG and WebP work out of
the box. HEIC/HEIF requires an additional Pillow plugin.
"""

from __future__ import annotations

import argparse
import json
import logging
import os
import tempfile
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from PIL import Image, ExifTags, ImageOps
from watchdog.events import FileSystemEventHandler
from watchdog.observers import Observer


DEFAULT_WIDTHS = (400, 800, 1200)
SUPPORTED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp"}

LOGGER = logging.getLogger("image-processor")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Process images for the image board.")
    parser.add_argument("--input", type=Path, required=True,
                        help="Directory containing original images.")
    parser.add_argument("--output", type=Path, required=True,
                        help="Directory containing generated image variants and images.config.json.")
    parser.add_argument("--poll-interval", type=float, default=2.0,
                        help="Seconds to wait before retrying a file that is still being copied.")
    return parser.parse_args()


def is_supported_image(path: Path) -> bool:
    return path.is_file() and path.suffix.lower() in SUPPORTED_EXTENSIONS


def image_key(path: Path) -> str:
    """Stable config key based on filename without extension."""
    return path.stem


def read_config(config_path: Path) -> list[dict[str, Any]]:
    if not config_path.exists():
        return []

    try:
        with config_path.open("r", encoding="utf-8") as f:
            data = json.load(f)
    except (json.JSONDecodeError, OSError) as exc:
        LOGGER.error("Could not read %s: %s", config_path, exc)
        return []

    if not isinstance(data, list):
        LOGGER.error("%s must contain a JSON array.", config_path)
        return []

    return [item for item in data if isinstance(item, dict)]


def write_config_atomic(config_path: Path, entries: list[dict[str, Any]]) -> None:
    config_path.parent.mkdir(parents=True, exist_ok=True)

    fd, temp_name = tempfile.mkstemp(
        prefix=".images.config.",
        suffix=".tmp",
        dir=config_path.parent,
        text=True,
    )

    os.chmod(temp_name, 0o644)

    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump(entries, f, indent=2, ensure_ascii=False)
            f.write("\n")
            f.flush()
            os.fsync(f.fileno())

        os.replace(temp_name, config_path)
    finally:
        try:
            os.unlink(temp_name)
        except FileNotFoundError:
            pass


def extract_date(path: Path) -> str:
    """
    Prefer EXIF DateTimeOriginal. Fall back to the file modification date.
    Returned format: YYYY-MM-DD.
    """
    try:
        with Image.open(path) as image:
            exif = image.getexif()

            date_tag = None
            for tag_id, tag_name in ExifTags.TAGS.items():
                if tag_name == "DateTimeOriginal":
                    date_tag = tag_id
                    break

            if date_tag is not None:
                value = exif.get(date_tag)
                if isinstance(value, str):
                    try:
                        return datetime.strptime(value, "%Y:%m:%d %H:%M:%S").date().isoformat()
                    except ValueError:
                        pass
    except Exception as exc:
        LOGGER.warning("Could not read EXIF date from %s: %s", path, exc)

    return datetime.fromtimestamp(path.stat().st_mtime, tz=timezone.utc).date().isoformat()


def wait_until_readable(path: Path, attempts: int = 10, delay: float = 1.0) -> bool:
    """
    A file may trigger a filesystem event before a large copy has finished.
    Try opening it a few times before processing.
    """
    previous_size = None

    for _ in range(attempts):
        try:
            size = path.stat().st_size
            with path.open("rb") as f:
                f.read(1)

            if size > 0 and size == previous_size:
                return True

            previous_size = size
        except OSError:
            pass

        time.sleep(delay)

    return False


def output_path(output_dir: Path, width: int, stem: str) -> Path:
    return output_dir / str(width) / f"{stem}.webp"


def create_variant(source: Path, destination: Path, width: int) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)

    with Image.open(source) as image:
        image = ImageOps.exif_transpose(image)
        image = image.convert("RGB")

        image.thumbnail((width, width), Image.Resampling.LANCZOS)

        image.save(
            destination,
            "WEBP",
            quality=85,
            method=6,
        )


def process_image(source: Path, output_dir: Path, config: list[dict[str, Any]]) -> None:
    stem = image_key(source)

    existing = next(
        (entry for entry in config if entry.get("name") == stem),
        None,
    )

    category = existing.get("category", "") if existing else ""

    # Preserve the first observed date. This prevents a later file timestamp
    # change from unexpectedly changing the displayed photo date.
    date = existing.get("date") if existing and existing.get("date") else extract_date(source)

    for width in DEFAULT_WIDTHS:
        destination = output_path(output_dir, width, stem)
        if not destination.exists():
            LOGGER.info("Generating %s px version of %s", width, source.name)
            create_variant(source, destination, width)

    # Record useful metadata without putting implementation-specific paths
    # into the config.
    with Image.open(source) as image:
        original_width, original_height = image.size

    entry = {
        "name": stem,
        "category": category,
        "date": date,
        "width": original_width,
        "height": original_height,
    }

    if existing:
        existing.clear()
        existing.update(entry)
    else:
        config.append(entry)

    config.sort(key=lambda item: (item.get("date", ""), item.get("name", "")))
    write_config_atomic(output_dir / "images.config.json", config)


def remove_deleted_images(input_dir: Path, output_dir: Path, config: list[dict[str, Any]]) -> None:
    existing_stems = {
        path.stem
        for path in input_dir.iterdir()
        if is_supported_image(path)
    }

    # Remove generated variants whose original no longer exists.
    for width in DEFAULT_WIDTHS:
        variant_dir = output_dir / str(width)
        if not variant_dir.exists():
            continue

        for variant in variant_dir.glob("*.webp"):
            if variant.stem not in existing_stems:
                LOGGER.info("Removing generated files for deleted image %s", variant.stem)
                variant.unlink(missing_ok=True)

    config[:] = [
        entry for entry in config
        if entry.get("name") in existing_stems
    ]


def synchronize(input_dir: Path, output_dir: Path) -> None:
    input_dir.mkdir(parents=True, exist_ok=True)
    output_dir.mkdir(parents=True, exist_ok=True)

    config_path = output_dir / "images.config.json"
    config = read_config(config_path)

    # Process all originals. This also makes startup recovery possible.
    for source in sorted(input_dir.iterdir()):
        if not is_supported_image(source):
            continue

        try:
            if wait_until_readable(source):
                process_image(source, output_dir, config)
            else:
                LOGGER.warning("Skipping unreadable/incomplete file: %s", source)
        except Exception:
            LOGGER.exception("Failed to process %s", source)

    remove_deleted_images(input_dir, output_dir, config)
    config.sort(key=lambda item: (item.get("date", ""), item.get("name", "")))
    write_config_atomic(config_path, config)


class ImageEventHandler(FileSystemEventHandler):
    def __init__(self, input_dir: Path, output_dir: Path):
        self.input_dir = input_dir
        self.output_dir = output_dir

    def handle(self, path: str) -> None:
        source = Path(path)

        if not source.is_relative_to(self.input_dir):
            return

        # A config change should not cause a recursive image-processing event.
        if source.name == "images.config.json":
            return

        # Re-synchronize instead of trying to maintain complicated incremental
        # state. The operation is cheap and idempotent for a normal photo set.
        synchronize(self.input_dir, self.output_dir)

    def on_created(self, event):
        if not event.is_directory:
            self.handle(event.src_path)

    def on_modified(self, event):
        if not event.is_directory:
            self.handle(event.src_path)

    def on_moved(self, event):
        if not event.is_directory:
            self.handle(event.dest_path)

    def on_deleted(self, event):
        if not event.is_directory:
            synchronize(self.input_dir, self.output_dir)


def main() -> None:
    args = parse_args()

    input_dir = args.input.resolve()
    output_dir = args.output.resolve()

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
    )

    LOGGER.info("Input directory:  %s", input_dir)
    LOGGER.info("Output directory: %s", output_dir)

    synchronize(input_dir, output_dir)

    observer = Observer()
    observer.schedule(
        ImageEventHandler(input_dir, output_dir),
        str(input_dir),
        recursive=False,
    )
    observer.start()

    LOGGER.info("Watching for new images...")

    try:
        while True:
            time.sleep(args.poll_interval)
    except KeyboardInterrupt:
        LOGGER.info("Stopping...")
        observer.stop()

    observer.join()


if __name__ == "__main__":
    main()
