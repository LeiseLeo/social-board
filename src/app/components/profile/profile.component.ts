import { Component, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { Observable } from 'rxjs';
import { ProfileService, ProfileConfig } from '../../services/profile.service';

@Component({
  selector: 'app-profile',
  standalone: true,
  templateUrl: './profile.component.html',
  styleUrls: ['./profile.component.scss'],
  imports: [CommonModule],
})
export class ProfileComponent {
  private profileService = inject(ProfileService);

  public profile$: Observable<ProfileConfig> = this.profileService.getProfile();
}
