import { Component, inject, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormBuilder, FormGroup, Validators, ReactiveFormsModule, FormsModule } from '@angular/forms';
import { HeaderComponent } from '../../shared/components/header/header.component';
import { SidebarComponent } from '../../shared/components/sidebar/sidebar.component';
import { AuthService } from '../../core/services/auth.service';
import { NotificationService } from '../../core/services/notification.service';
import { User } from '../../core/models/user.model';

@Component({
  selector: 'app-settings',
  standalone: true,
  imports: [CommonModule, ReactiveFormsModule, HeaderComponent, SidebarComponent, FormsModule],
  templateUrl: './settings.component.html',
  styleUrls: ['./settings.component.scss']
})
export class SettingsComponent implements OnInit {
  private fb = inject(FormBuilder);
  private authService = inject(AuthService);
  private notificationService = inject(NotificationService);

  sidebarOpen = true;
  isUpdating = false;
  currentUser: User | null = null;
  
  profileForm: FormGroup;
  notificationPreferences = {
    email: true,
    sms: true,
    push: true,
    reports: true
  };

  constructor() {
    this.profileForm = this.fb.group({
      full_name: ['', Validators.required],
      email: ['', [Validators.required, Validators.email]],
      phone_number: ['', Validators.required],
      age: [''],
      gender: [''],
      marital_status: [''],
      profession: ['']
    });
  }

  ngOnInit() {
    this.authService.currentUser$.subscribe(user => {
      if (user) {
        this.currentUser = user;
        this.profileForm.patchValue(user);
      }
    });
  }

  toggleSidebar() {
    this.sidebarOpen = !this.sidebarOpen;
  }

  onUpdateProfile() {
    if (this.profileForm.valid) {
      this.isUpdating = true;
      
      this.authService.updateProfile(this.profileForm.value).subscribe({
        next: (user) => {
          this.notificationService.success('Profile updated successfully');
          this.isUpdating = false;
        },
        error: (error) => {
          this.notificationService.error('Failed to update profile');
          this.isUpdating = false;
        }
      });
    }
  }

  onPhotoSelected(event: any) {
    const file = event.target.files[0];
    if (file) {
      // Handle photo upload
      this.notificationService.info('Photo upload feature coming soon');
    }
  }
}
