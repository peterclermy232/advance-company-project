import { Component, inject, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormBuilder, FormGroup, Validators, ReactiveFormsModule } from '@angular/forms';
import { Router, RouterModule } from '@angular/router';
import { AuthService } from '../../../core/services/auth.service';
import { NotificationService } from '../../../core/services/notification.service';

@Component({
  selector: 'app-login',
  standalone: true,
  imports: [CommonModule, ReactiveFormsModule, RouterModule],
  templateUrl: './login.component.html',
  styleUrls: ['./login.component.scss']
})
export class LoginComponent implements OnInit {
  private fb = inject(FormBuilder);
  private authService = inject(AuthService);
  private router = inject(Router);
  private notificationService = inject(NotificationService);

  loginForm!: FormGroup;
  isLoading = false;
  showPassword = false;
  show2FAModal = false;
  twoFactorCode = '';

  ngOnInit(): void {
    this.loginForm = this.fb.group({
      email: ['', [Validators.required, Validators.email]],
      password: ['', [Validators.required, Validators.minLength(6)]],
      remember: [false]
    });
  }

  onSubmit(): void {
    if (this.loginForm.invalid) {
      Object.keys(this.loginForm.controls).forEach(key => {
        this.loginForm.get(key)?.markAsTouched();
      });
      return;
    }

    this.isLoading = true;

    const credentials = {
      email: this.loginForm.get('email')?.value,
      password: this.loginForm.get('password')?.value
    };

    this.authService.login(credentials).subscribe({
      next: (response: any) => {
        // Check if 2FA is required
        if (response.requires_2fa) {
          this.show2FAModal = true;
          this.isLoading = false;
          this.notificationService.info('Please enter your 2FA code');
        } else {
          // Login successful, navigate to dashboard
          this.notificationService.success('Login successful! 👋');
          this.router.navigate(['/dashboard']);
          this.isLoading = false;
        }
      },
      error: (error) => {
        const message = error.error?.error || 
                       error.error?.detail || 
                       'Invalid email or password';
        this.notificationService.error(message);
        this.isLoading = false;
      }
    });
  }

  verify2FA(isBackupCode = false): void {
    if (!this.twoFactorCode) {
      this.notificationService.error('Please enter a code');
      return;
    }

    this.isLoading = true;
    this.authService.verify2FA(this.twoFactorCode, isBackupCode).subscribe({
      next: () => {
        this.show2FAModal = false;
        this.notificationService.success('2FA verified successfully! ✓');
        this.router.navigate(['/dashboard']);
        this.isLoading = false;
      },
      error: (error) => {
        const message = error.error?.error || 'Invalid verification code';
        this.notificationService.error(message);
        this.isLoading = false;
      }
    });
  }

  cancel2FA(): void {
    this.show2FAModal = false;
    this.twoFactorCode = '';
    this.isLoading = false;
  }

  getErrorMessage(fieldName: string): string {
    const control = this.loginForm.get(fieldName);
    
    if (control?.hasError('required')) {
      return `${fieldName} is required`;
    }
    if (control?.hasError('email')) {
      return 'Please enter a valid email';
    }
    if (control?.hasError('minlength')) {
      return `${fieldName} must be at least 6 characters`;
    }
    return '';
  }

  togglePassword(): void {
    this.showPassword = !this.showPassword;
  }
}