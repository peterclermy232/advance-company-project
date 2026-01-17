import { Component, inject, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormBuilder, FormGroup, Validators, ReactiveFormsModule, FormsModule } from '@angular/forms';
import { HeaderComponent } from '../../shared/components/header/header.component';
import { SidebarComponent } from '../../shared/components/sidebar/sidebar.component';
import { AuthService } from '../../core/services/auth.service';
import { NotificationService } from '../../core/services/notification.service';
import { User } from '../../core/models/user.model';
import { environment } from '../../environments/environment';
import { ProfileAvatarComponent } from '../../shared/components/profile-avatar/profile-avatar.component';

@Component({
  selector: 'app-settings',
  standalone: true,
  imports: [CommonModule, ReactiveFormsModule, FormsModule, HeaderComponent, SidebarComponent,ProfileAvatarComponent],
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
  
  // Modal states
  showPasswordModal = false;
  show2FAModal = false;
  showDeleteModal = false;
  
  // 2FA Setup
  qrCodeUrl: string | null = null;
  secretKey: string | null = null;
  backupCodes: string[] = [];
  show2FASetup = false;
  
  profileForm: FormGroup;
  passwordForm: FormGroup;
  twoFactorForm: FormGroup;
  deleteAccountForm: FormGroup;
  
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

    this.passwordForm = this.fb.group({
      current_password: ['', Validators.required],
      new_password: ['', [Validators.required, Validators.minLength(8)]],
      confirm_password: ['', Validators.required]
    }, { validators: this.passwordMatchValidator });

    this.twoFactorForm = this.fb.group({
      code: ['', [Validators.required, Validators.minLength(6), Validators.maxLength(6)]]
    });

    this.deleteAccountForm = this.fb.group({
      password: ['', Validators.required],
      confirmation: ['', [Validators.required, Validators.pattern(/^DELETE$/)]]
    });
  }

  ngOnInit() {
    this.authService.currentUser$.subscribe(user => {
      if (user) {
        this.currentUser = user;
        this.profileForm.patchValue({
          full_name: user.full_name || '',
          email: user.email || '',
          phone_number: user.phone_number || '',
          age: user.age || '',
          gender: user.gender || '',
          marital_status: user.marital_status || '',
          profession: user.profession || ''
        });
      }
    });
  }

  passwordMatchValidator(group: FormGroup) {
    const newPassword = group.get('new_password')?.value;
    const confirmPassword = group.get('confirm_password')?.value;
    return newPassword === confirmPassword ? null : { passwordMismatch: true };
  }

  toggleSidebar() {
    this.sidebarOpen = !this.sidebarOpen;
  }

  getProfilePhotoUrl(photoPath: string): string {
    if (photoPath.startsWith('http://') || photoPath.startsWith('https://')) {
      return photoPath;
    }
    const cleanPath = photoPath.startsWith('/') ? photoPath.substring(1) : photoPath;
    return `${environment.apiUrl}/${cleanPath}`;
  }

  onPhotoSelected(event: Event) {
    const input = event.target as HTMLInputElement;
    const file = input.files?.[0];
    
    if (file) {
      if (!file.type.startsWith('image/')) {
        this.notificationService.error('Please select an image file');
        input.value = '';
        return;
      }
      
      const maxSize = 5 * 1024 * 1024;
      if (file.size > maxSize) {
        this.notificationService.error('Image size should be less than 5MB');
        input.value = '';
        return;
      }
      
      this.selectedPhoto = file;
      
      const reader = new FileReader();
      reader.onload = (e: ProgressEvent<FileReader>) => {
        this.photoPreview = e.target?.result as string;
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
  if (this.profileForm.invalid) {
    this.notificationService.error('Please fill in all required fields correctly');
    return;
  }

  this.isUpdating = true;

  if (this.selectedPhoto) {
    // Upload photo separately first
    this.authService.uploadProfilePhoto(this.selectedPhoto).subscribe({
      next: (user) => {
        // Then update other profile fields
        this.updateProfileFields();
      },
      error: (error) => {
        console.error('Photo upload error:', error);
        this.isUpdating = false;
      }
    });
  } else {
    // Just update profile fields
    this.updateProfileFields();
  }
}

private updateProfileFields() {
  const userId = this.currentUser?.id;
  if (!userId) {
    this.isUpdating = false;
    return;
  }

  this.authService.updateProfile(userId, this.profileForm.value).subscribe({
    next: (user) => {
      this.currentUser = user;
      this.selectedPhoto = null;
      this.photoPreview = null;
      this.isUpdating = false;
      
      // Clear file input
      const fileInput = document.querySelector('input[type="file"]') as HTMLInputElement;
      if (fileInput) {
        fileInput.value = '';
      }
    },
    error: (error) => {
      console.error('Profile update error:', error);
      this.isUpdating = false;
    }
  });
}

// Add method to delete photo
deleteProfilePhoto() {
  const confirmed = confirm('Are you sure you want to delete your profile photo?');
  if (!confirmed) return;

  this.authService.deleteProfilePhoto().subscribe({
    next: () => {
      if (this.currentUser) {
        this.currentUser.profile_photo = null;
        this.currentUser.profile_photo_url = null;
      }
      this.selectedPhoto = null;
      this.photoPreview = null;
      
      const fileInput = document.querySelector('input[type="file"]') as HTMLInputElement;
      if (fileInput) {
        fileInput.value = '';
      }
    },
    error: (error) => {
      console.error('Failed to delete photo:', error);
    }
  });
}


  // Password Change
  openPasswordModal() {
    this.showPasswordModal = true;
    this.passwordForm.reset();
  }

  closePasswordModal() {
    this.showPasswordModal = false;
    this.passwordForm.reset();
  }

  onChangePassword() {
    if (this.passwordForm.invalid) {
      this.notificationService.error('Please fill in all fields correctly');
      return;
    }

    if (this.passwordForm.hasError('passwordMismatch')) {
      this.notificationService.error('Passwords do not match');
      return;
    }

    const loadingToast = this.notificationService.loading('Changing password...');

    this.authService.changePassword(this.passwordForm.value).subscribe({
      next: (response) => {
        loadingToast.dismiss();
        this.notificationService.success('✓ Password changed successfully! Please login again.');
        this.closePasswordModal();
        setTimeout(() => {
          this.authService.logout();
        }, 2000);
      },
      error: (error) => {
        loadingToast.dismiss();
        const errorMessage = error.error?.error || 
                           (Array.isArray(error.error?.error) ? error.error.error.join(', ') : '') ||
                           'Failed to change password';
        this.notificationService.error(errorMessage);
      }
    });
  }


  // Two-Factor Authentication
  open2FAModal() {
    this.show2FAModal = true;
    this.show2FASetup = false;
    this.twoFactorForm.reset();
  }

  close2FAModal() {
    this.show2FAModal = false;
    this.show2FASetup = false;
    this.qrCodeUrl = null;
    this.secretKey = null;
    this.backupCodes = [];
    this.twoFactorForm.reset();
  }

  enable2FA() {
    const loadingToast = this.notificationService.loading('Setting up 2FA...');
    
    this.authService.enable2FA().subscribe({
      next: (response) => {
        loadingToast.dismiss();
        this.qrCodeUrl = response.qr_code;
        this.secretKey = response.secret;
        this.show2FASetup = true;
        this.notificationService.info('Scan the QR code with your authenticator app');
      },
      error: (error) => {
        loadingToast.dismiss();
        this.notificationService.error('Failed to enable 2FA');
      }
    });
  }

  confirm2FA() {
    if (this.twoFactorForm.invalid) {
      this.notificationService.error('Please enter a valid 6-digit code');
      return;
    }

    const loadingToast = this.notificationService.loading('Verifying code...');

    this.authService.confirm2FA(this.twoFactorForm.value.code).subscribe({
      next: (response) => {
        loadingToast.dismiss();
        this.backupCodes = response.backup_codes;
        this.notificationService.success('✓ 2FA enabled successfully! Save your backup codes.');
        if (this.currentUser) {
          this.currentUser.two_factor_enabled = true;
        }
      },
      error: (error) => {
        loadingToast.dismiss();
        this.notificationService.error('Invalid verification code');
      }
    });
  }

  disable2FA() {
    const password = prompt('🔐 Enter your password to disable 2FA:');
    if (!password) return;

    const loadingToast = this.notificationService.loading('Disabling 2FA...');

    this.authService.disable2FA(password).subscribe({
      next: () => {
        loadingToast.dismiss();
        this.notificationService.success('✓ 2FA disabled successfully');
        if (this.currentUser) {
          this.currentUser.two_factor_enabled = false;
        }
        this.close2FAModal();
      },
      error: (error) => {
        loadingToast.dismiss();
        this.notificationService.error('Failed to disable 2FA. Please check your password.');
      }
    });
  }
  copyBackupCodes() {
    const codesText = this.backupCodes.join('\n');
    navigator.clipboard.writeText(codesText).then(() => {
      this.notificationService.success('✓ Backup codes copied to clipboard!');
    }).catch(() => {
      this.notificationService.error('Failed to copy codes');
    });
  }


  downloadBackupCodes() {
    const codesText = this.backupCodes.join('\n');
    const blob = new Blob([codesText], { type: 'text/plain' });
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = '2fa-backup-codes.txt';
    a.click();
    window.URL.revokeObjectURL(url);
    this.notificationService.success('Backup codes downloaded');
  }

  // Delete Account
  openDeleteModal() {
    this.showDeleteModal = true;
    this.deleteAccountForm.reset();
  }

  closeDeleteModal() {
    this.showDeleteModal = false;
    this.deleteAccountForm.reset();
  }

  onDeleteAccount() {
    if (this.deleteAccountForm.invalid) {
      this.notificationService.error('Please complete all fields correctly');
      return;
    }

    const confirmed = confirm('Are you absolutely sure? This action cannot be undone!');
    if (!confirmed) return;

    this.authService.deleteAccount(this.deleteAccountForm.value).subscribe({
      next: () => {
        this.notificationService.success('Account deleted successfully');
        this.closeDeleteModal();
        setTimeout(() => {
          this.authService.logout();
        }, 2000);
      },
      error: (error) => {
        const errorMessage = error.error?.error || 'Failed to delete account';
        this.notificationService.error(errorMessage);
      }
    });
  }

  saveNotificationPreferences() {
    // TODO: Implement API call to save notification preferences
    this.notificationService.success('Notification preferences saved');
  }
}