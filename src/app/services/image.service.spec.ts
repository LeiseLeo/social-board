import { TestBed } from '@angular/core/testing';
import { HttpClientTestingModule } from '@angular/common/http/testing';
import { ImageService, ImageConfig } from './image.service';

describe('ImageService', () => {
  let service: ImageService;

  beforeEach(() => {
    TestBed.configureTestingModule({
      imports: [HttpClientTestingModule],
    });

    service = TestBed.inject(ImageService);
  });

  it('sorts images by date descending', () => {
    const images: ImageConfig[] = [
      { name: 'older', category: '', date: '2026-08-01', width: 1, height: 1 },
      { name: 'newest', category: '', date: '2026-08-10', width: 1, height: 1 },
      { name: 'middle', category: '', date: '2026-08-05', width: 1, height: 1 },
    ];

    const result = service.sortImages(images);

    expect(result.map((image) => image.name)).toEqual(['newest', 'middle', 'older']);
  });

  it('filters out images without a category for story view', () => {
    const images: ImageConfig[] = [
      { name: 'without-category', category: '', date: '2026-08-10', width: 1, height: 1 },
      { name: 'with-category', category: 'summer', date: '2026-08-09', width: 1, height: 1 },
      {
        name: 'another-with-category',
        category: 'winter',
        date: '2026-08-08',
        width: 1,
        height: 1,
      },
    ];

    const result = service.getStoryImages(images);

    expect(result.map((image) => image.name)).toEqual(['with-category', 'another-with-category']);
  });
});
