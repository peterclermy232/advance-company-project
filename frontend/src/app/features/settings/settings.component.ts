import { Component, inject, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormBuilder, FormGroup, Validators, ReactiveFormsModule, FormsModule } from '@angular/forms';
import { HeaderComponent } from '../../shared/components/header/header.component';
import { SidebarComponent } from '../../shared/components/sidebar/sidebar.component';
import { AuthService } from '../../core/services/auth.service';
import { NotificationService } from '../../core/services/notification.service';
import { User } from '../../core/models/user.model';
import { environment } from '../../environments/environment';


@Component({
  selector: 'app-settings',
  standalone: true,
  imports: [CommonModule, ReactiveFormsModule, FormsModule, HeaderComponent, SidebarComponent],
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
  selectedPhoto: File | null = null;
  photoPreview: string | null = null;
  
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

  getProfilePhotoUrl(photoPath: string): string {
    // If it's already a full URL, return as is
    if (photoPath.startsWith('http://') || photoPath.startsWith('https://')) {
      return photoPath;
    }
    // Otherwise, prepend your API base URL
    return `${environment.apiUrl}${photoPath}`;
  }

  onPhotoSelected(event: any) {
    const file = event.target.files[0];
    if (file) {
      // Validate file type
      if (!file.type.startsWith('image/')) {
        this.notificationService.error('Please select an image file');
        return;
      }
      
      // Validate file size (5MB limit)
      if (file.size > 5 * 1024 * 1024) {
        this.notificationService.error('Image size should be less than 5MB');
        return;
      }
      
      this.selectedPhoto = file;
      
      // Create preview
      const reader = new FileReader();
      reader.onload = (e: any) => {
        this.photoPreview = e.target.result;
      };
      reader.readAsDataURL(file);
      
      this.notificationService.info('Photo selected. Click "Save Changes" to upload');
    }
  }

  clearPhotoSelection(fileInput: HTMLInputElement) {
    this.selectedPhoto = null;
    this.photoPreview = null;
    fileInput.value = '';
    this.notificationService.info('Photo selection cleared');
  }

  onUpdateProfile() {
    if (this.profileForm.valid) {
      this.isUpdating = true;
      
      // Create FormData for multipart upload
      const formData = new FormData();
      
      // Append all form fields
      Object.keys(this.profileForm.value).forEach(key => {
        const value = this.profileForm.value[key];
        if (value !== null && value !== '') {
          formData.append(key, value);
        }
      });
      
      // Append photo if selected
      if (this.selectedPhoto) {
        formData.append('profile_photo', this.selectedPhoto);
      }
      
      this.authService.updateProfileWithPhoto(formData).subscribe({
        next: (user) => {
          this.notificationService.success('Profile updated successfully');
          this.selectedPhoto = null;
          this.photoPreview = null;
          this.isUpdating = false;
        },
        error: (error) => {
          this.notificationService.error('Failed to update profile');
          this.isUpdating = false;
        }
      });
    }
  }
}