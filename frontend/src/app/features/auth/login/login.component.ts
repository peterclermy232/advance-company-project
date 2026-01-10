import { Component, inject, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormBuilder, FormGroup, Validators, ReactiveFormsModule } from '@angular/forms';
import { Router, RouterModule } from '@angular/router';

import { AuthService } from '../../../core/services/auth.service';
import { BiometricAuthService } from '../../../core/services/biometric-auth.service';
import { NotificationService } from '../../../core/services/notification.service';

interface BiometricLoginResponse {
  tokens: {
    access: string;
    refresh: string;
  };
}

@Component({
  selector: 'app-login',
  standalone: true,
  imports: [CommonModule, ReactiveFormsModule, RouterModule],
  templateUrl: './login.component.html',
  styleUrls: ['./login.component.scss']
})
export class LoginComponent implements OnInit {

  private fb: FormBuilder = inject(FormBuilder);
  private authService: AuthService = inject(AuthService);
  private biometricService: BiometricAuthService = inject(BiometricAuthService);
  private router: Router = inject(Router);
  private notificationService: NotificationService = inject(NotificationService);

  loginForm!: FormGroup;

  biometricAvailable = false;
  availableBiometrics = { fingerprint: false, faceId: false };
  savedBiometricDevices: any[] = [];
  showBiometricOptions = false;

  isLoading = false;
  showPassword = false;

  ngOnInit(): void {
    this.loginForm = this.fb.group({
      email: ['', [Validators.required, Validators.email]],
      password: ['', [Validators.required, Validators.minLength(6)]],
      remember: [false]
    });

    this.biometricAvailable = this.biometricService.isBiometricAvailable();

    if (this.biometricAvailable) {
      this.biometricService
        .detectAvailableBiometrics()
        .then(result => {
          this.availableBiometrics = result;
          this.loadSavedBiometricDevices();
        });
    }
  }

  loadSavedBiometricDevices(): void {
    const saved = localStorage.getItem('biometric_devices');
    if (saved) {
      this.savedBiometricDevices = JSON.parse(saved);
      this.showBiometricOptions = this.savedBiometricDevices.length > 0;
    }
  }

  onSubmit(): void {
    if (this.loginForm.invalid) return;

    this.isLoading = true;

    this.authService.login(this.loginForm.value).subscribe({
      next: () => {
        this.notificationService.success('Login successful');
        this.router.navigate(['/dashboard']);
      },
      error: () => {
        this.notificationService.error('Invalid email or password');
        this.isLoading = false;
      },
      complete: () => (this.isLoading = false)
    });
  }

  async onBiometricLogin(type: 'fingerprint' | 'face_id'): Promise<void> {
    const email = this.loginForm.get('email')?.value;
    if (!email) {
      this.notificationService.error('Enter email first');
      return;
    }

    const device = this.savedBiometricDevices.find(
      d => d.device_type === type && d.email === email
    );

    if (!device) {
      this.notificationService.error('No biometric device found');
      return;
    }

    this.isLoading = true;

    this.biometricService
      .biometricLogin(email, device.device_id)
      .subscribe({
        next: (response: BiometricLoginResponse) => {
          localStorage.setItem('access_token', response.tokens.access);
          localStorage.setItem('refresh_token', response.tokens.refresh);
          this.notificationService.success('Biometric login successful');
          this.router.navigate(['/dashboard']);
        },
        error: () => {
          this.notificationService.error('Biometric authentication failed');
          this.isLoading = false;
        },
        complete: () => (this.isLoading = false)
      });
  }

  getErrorMessage(fieldName: string): string { const control = this.loginForm.get(fieldName);
     if (control?.hasError('required')) { return `${fieldName} is required`; } 
     if (control?.hasError('email')) { return 'Please enter a valid email'; } 
     if (control?.hasError('minlength')) { return `${fieldName} must be at least 6 characters`; } return ''; }

  togglePassword(): void {
    this.showPassword = !this.showPassword;
  }
}
