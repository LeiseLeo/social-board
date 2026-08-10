import { Injectable, inject } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';
import { environment } from '../../environments/environment';

export interface ImageConfig {
  name: string;
  category: string;
  date: string;
  width: number;
  height: number;
}

@Injectable({
  providedIn: 'root',
})
export class ImageService {
  private http = inject(HttpClient);

  getImages(): Observable<ImageConfig[]> {
    return this.http.get<ImageConfig[]>(environment.imagesConfigUrl);
  }

  sortImages(images: ImageConfig[]): ImageConfig[] {
    return [...images].sort((a, b) => {
      const dateA = new Date(a.date).getTime();
      const dateB = new Date(b.date).getTime();

      return dateB - dateA;
    });
  }

  getStoryImages(images: ImageConfig[]): ImageConfig[] {
    return this.sortImages(images).filter((image) => Boolean(image.category));
  }

  getImageUrl(image: ImageConfig, resolution: 400 | 800 | 1200 = 800): string {
    return `${environment.imagesBaseUrl}/${resolution}/${image.name}.webp`;
  }
}
