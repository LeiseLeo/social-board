import { Component, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { Observable } from 'rxjs';
import { ProfileService, ProfileConfig } from '../../services/profile.service';

@Component({
  selector: 'app-header',
  standalone: true,
  templateUrl: './header.component.html',
  styleUrls: ['./header.component.scss'],
  imports: [CommonModule],
})
export class HeaderComponent {
  private profileService = inject(ProfileService);

  public profile$: Observable<ProfileConfig> = this.profileService.getProfile();
}
