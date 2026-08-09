import { Injectable, inject } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable, map } from 'rxjs';
import { environment } from '../../environments/environment';

export interface ProfileConfig {
  appName: string;
  username: string;
  profilePicture: string;
}

@Injectable({
  providedIn: 'root',
})
export class ProfileService {
  private http = inject(HttpClient);

  getProfile(): Observable<ProfileConfig> {
    return this.http.get<ProfileConfig>(environment.profileConfigUrl).pipe(
      map((p) => ({
        ...p,
        profilePicture: `${environment.profileImageBaseUrl}/${p['profilePicture']}`,
      })),
    );
  }
}
