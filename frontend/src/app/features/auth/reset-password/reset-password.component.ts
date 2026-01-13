
import { Component, inject, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormBuilder, FormGroup, Validators, ReactiveFormsModule } from '@angular/forms';
import { Router, ActivatedRoute, RouterModule } from '@angular/router';
import { HttpClient } from '@angular/common/http';
import { environment } from '../../../environments/environment';
import { NotificationService } from '../../../core/services/notification.service';

@Component({
  selector: 'app-reset-password',
  standalone: true,
  imports: [CommonModule, ReactiveFormsModule, RouterModule],
  templateUrl: './reset-password.component.html',
  styleUrls: ['./reset-password.component.scss']
})
export class ResetPasswordComponent implements OnInit {
  private fb = inject(FormBuilder);
  private http = inject(HttpClient);
  private router = inject(Router);
  private route = inject(ActivatedRoute);
  private notificationService = inject(NotificationService);

  resetPasswordForm: FormGroup;
  isLoading = false;
  resetSuccess = false;
  showPassword = false;
  showConfirmPassword = false;

  uid: string | null = null;
  token: string | null = null;

  // Password strength indicators
  hasMinLength = false;
  hasUpperCase = false;
  hasLowerCase = false;
  hasNumber = false;

  constructor() {
    this.resetPasswordForm = this.fb.group({
      new_password: ['', [Validators.required, Validators.minLength(8)]],
      confirm_password: ['', [Validators.required]]
    }, { validators: this.passwordMatchValidator });

    // Monitor password changes for strength indicator
    this.resetPasswordForm.get('new_password')?.valueChanges.subscribe(password => {
      this.checkPasswordStrength(password);
    });
  }

  ngOnInit(): void {
    // Get uid and token from query params
    this.route.queryParams.subscribe(params => {
      this.uid = params['uid'];
      this.token = params['token'];
    });
  }

  passwordMatchValidator(form: FormGroup) {
    const password = form.get('new_password');
    const confirmPassword = form.get('confirm_password');
    
    if (password?.value !== confirmPassword?.value) {
      confirmPassword?.setErrors({ mismatch: true });
      return { mismatch: true };
    }
    return null;
  }

  checkPasswordStrength(password: string): void {
    this.hasMinLength = password.length >= 8;
    this.hasUpperCase = /[A-Z]/.test(password);
    this.hasLowerCase = /[a-z]/.test(password);
    this.hasNumber = /[0-9]/.test(password);
  }

  getConfirmPasswordError(): string {
    const control = this.resetPasswordForm.get('confirm_password');
    if (control?.hasError('required')) {
      return 'Please confirm your password';
    }
    if (control?.hasError('mismatch')) {
      return 'Passwords do not match';
    }
    return '';
  }

  onSubmit(): void {
    if (this.resetPasswordForm.invalid || !this.uid || !this.token) return;

    this.isLoading = true;

    const payload = {
      uid: this.uid,
      token: this.token,
      new_password: this.resetPasswordForm.get('new_password')?.value
    };

    this.http.post(`${environment.apiUrl}/auth/users/reset_password_confirm/`, payload)
      .subscribe({
        next: () => {
          this.resetSuccess = true;
          this.isLoading = false;
          this.notificationService.success('Password reset successful! 🎉');
        },
        error: (error) => {
          this.isLoading = false;
          const errorMessage = error.error?.error || 
                             error.error?.detail || 
                             'Failed to reset password. The link may have expired.';
          this.notificationService.error(errorMessage);
        }
      });
  }

  togglePassword(): void {
    this.showPassword = !this.showPassword;
  }

  toggleConfirmPassword(): void {
    this.showConfirmPassword = !this.showConfirmPassword;
  }

  goToLogin(): void {
    this.router.navigate(['/auth/login']);
  }
}