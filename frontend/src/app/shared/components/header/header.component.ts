import { Component, inject, Output, EventEmitter, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { AuthService } from '../../../core/services/auth.service';
import { User } from '../../../core/models/user.model';
import { NotificationDropdownComponent } from '../notification-dropdown/notification-dropdown.component';
import { ProfileAvatarComponent } from '../profile-avatar/profile-avatar.component';

@Component({
  selector: 'app-header',
  standalone: true,
  imports: [CommonModule, NotificationDropdownComponent,ProfileAvatarComponent],
  templateUrl: './header.component.html',
  styleUrls: ['./header.component.scss']
})
export class HeaderComponent implements OnInit {
  @Output() toggleSidebar = new EventEmitter<void>();
  
  authService = inject(AuthService);
  currentUser: User | null = null;

  ngOnInit() {
    this.authService.currentUser$.subscribe(user => {
      this.currentUser = user;
    });
  }

  onToggleSidebar() {
    this.toggleSidebar.emit();
  }

  logout() {
    this.authService.logout();
  }
}
