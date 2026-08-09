import { Component } from '@angular/core';
import { HeaderComponent } from './components/header/header.component';
import { ProfileComponent } from './components/profile/profile.component';
import { TabsComponent } from './components/tabs/tabs.component';
import { BoardComponent } from './components/board/board.component';
import { StoryComponent } from './components/story/story.component';

@Component({
  selector: 'app-root',
  standalone: true,
  imports: [HeaderComponent, ProfileComponent, TabsComponent, BoardComponent, StoryComponent],
  templateUrl: './app.html',
  styleUrl: './app.css',
})
export class App {
  activeTab = 'board';

  setActiveTab(tab: string) {
    this.activeTab = tab;
  }
}
