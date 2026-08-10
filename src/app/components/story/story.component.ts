import { Component, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { Observable, map } from 'rxjs';
import { ImageService, ImageConfig } from '../../services/image.service';

interface CategoryGroup {
  category: string;
  images: ImageConfig[];
  preview: ImageConfig;
}

@Component({
  selector: 'app-story',
  standalone: true,
  imports: [CommonModule],
  templateUrl: './story.component.html',
  styleUrls: ['./story.component.scss'],
})
export class StoryComponent {
  private imageService = inject(ImageService);

  public groups$: Observable<CategoryGroup[]> = this.imageService.getImages().pipe(
    map((images) => {
      const storyImages = this.imageService.getStoryImages(images);
      const map = new Map<string, ImageConfig[]>();
      for (const img of storyImages) {
        const list = map.get(img.category) || [];
        list.push(img);
        map.set(img.category, list);
      }

      return Array.from(map.entries()).map(([category, imgs]) => ({
        category,
        images: imgs,
        preview: imgs[0],
      }));
    }),
  );

  // viewer state
  public viewerOpen = false;
  public viewerImages: ImageConfig[] = [];
  public viewerIndex = 0;

  openViewer(group: CategoryGroup, index = 0) {
    this.viewerImages = group.images;
    this.viewerIndex = index;
    this.viewerOpen = true;
  }

  closeViewer() {
    this.viewerOpen = false;
  }

  prev() {
    if (!this.viewerImages.length) return;
    this.viewerIndex = (this.viewerIndex - 1 + this.viewerImages.length) % this.viewerImages.length;
  }

  next() {
    if (!this.viewerImages.length) return;
    this.viewerIndex = (this.viewerIndex + 1) % this.viewerImages.length;
  }

  getImageUrl(img: ImageConfig | undefined) {
    if (!img) return '';
    return this.imageService.getImageUrl(img);
  }
}
