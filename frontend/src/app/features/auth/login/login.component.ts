import { Component, inject, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormBuilder, FormGroup, Validators, ReactiveFormsModule } from '@angular/forms';
import { Router, RouterModule } from '@angular/router';
import { AuthService } from '../../../core/services/auth.service';
import { ToastService } from '../../../core/services/toast.service';

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
  private toastService = inject(ToastService);

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
      this.toastService.warning('Please fill in all required fields correctly');
      return;
    }

    this.isLoading = true;

    const credentials = {
      email: this.loginForm.get('email')?.value,
      password: this.loginForm.get('password')?.value
    };

    this.authService.login(credentials).subscribe({
      next: (response: any) => {
        this.isLoading = false;

        // Backend response shape:
        // { success, message, toast_type, data: { user, tokens, requires_2fa } }

        // 2FA required
        if (response?.data?.requires_2fa) {
          this.show2FAModal = true;
          this.toastService.info(response?.message || 'Two-factor authentication required.');
          return;
        }

        // Show message from backend
        const toastType = response?.toast_type || 'success';
        const message = response?.message || 'Login successful! Welcome back 👋';

        if (toastType === 'success') this.toastService.success(message);
        else if (toastType === 'info') this.toastService.info(message);
        else if (toastType === 'warning') this.toastService.warning(message);
        else this.toastService.success(message);

        setTimeout(() => {
          this.router.navigate(['/dashboard']);
        }, 600);
      },
      error: (error) => {
        this.isLoading = false;

        // Email not verified — redirect to verify-email page
        if (error.status === 403 && error.error?.data?.email_verified === false) {
          const email = error.error?.data?.email;
          this.toastService.warning(
            error.error?.message || 'Please verify your email before logging in. Check your inbox.'
          );
          this.router.navigate(['/auth/verify-email'], {
            queryParams: { email }
          });
          return;
        }

        // Show backend error message
        const errorMessage = error.error?.message ||
                             error.error?.detail ||
                             error.error?.error ||
                             'Login failed. Please try again.';
        this.toastService.error(errorMessage);
      }
    });
  }

  verify2FA(isBackupCode = false): void {
    if (!this.twoFactorCode || this.twoFactorCode.trim().length === 0) {
      this.toastService.warning('Please enter a verification code');
      return;
    }

    this.isLoading = true;

    this.authService.verify2FA(this.twoFactorCode, isBackupCode).subscribe({
      next: (response: any) => {
        this.isLoading = false;
        this.show2FAModal = false;

        // Show backend message
        this.toastService.success(response?.message || 'Verification successful!');

        setTimeout(() => {
          this.router.navigate(['/dashboard']);
        }, 600);
      },
      error: (error) => {
        this.isLoading = false;
        const errorMessage = error.error?.message ||
                             error.error?.detail ||
                             'Invalid verification code. Please try again.';
        this.toastService.error(errorMessage);
      }
    });
  }

  cancel2FA(): void {
    this.show2FAModal = false;
    this.twoFactorCode = '';
    this.isLoading = false;
    this.toastService.info('2FA verification cancelled');
  }

  getErrorMessage(fieldName: string): string {
    const control = this.loginForm.get(fieldName);
    if (control?.hasError('required')) {
      return `${fieldName.charAt(0).toUpperCase() + fieldName.slice(1)} is required`;
    }
    if (control?.hasError('email')) {
      return 'Please enter a valid email address';
    }
    if (control?.hasError('minlength')) {
      const minLength = control.errors?.['minlength']?.requiredLength;
      return `${fieldName.charAt(0).toUpperCase() + fieldName.slice(1)} must be at least ${minLength} characters`;
    }
    return '';
  }

  togglePassword(): void {
    this.showPassword = !this.showPassword;
  }
}