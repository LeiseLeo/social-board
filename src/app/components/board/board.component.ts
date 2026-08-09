import { Component, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { Observable } from 'rxjs';
import { ImageConfig } from '../../models/image.model';
import { ImageService } from '../../services/image.service';

@Component({
  selector: 'app-board',
  standalone: true,
  templateUrl: './board.component.html',
  styleUrls: ['./board.component.scss'],
  imports: [CommonModule],
})
export class BoardComponent {
  public imageService = inject(ImageService);

  public images$: Observable<ImageConfig[]> = this.imageService.getImages();
  public viewerOpen = false;
  public viewerImages: ImageConfig[] = [];
  public viewerIndex = 0;

  trackByName(_: number, item: ImageConfig) {
    return item.name;
  }

  openViewer(images: ImageConfig[], index: number) {
    this.viewerImages = images;
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
}
