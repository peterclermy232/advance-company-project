// forgot-password.component.ts
import { Component, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormBuilder, FormGroup, Validators, ReactiveFormsModule } from '@angular/forms';
import { RouterModule } from '@angular/router';
import { AuthService } from '../../../core/services/auth.service';
import { NotificationService } from '../../../core/services/notification.service';

@Component({
  selector: 'app-forgot-password',
  standalone: true,
  imports: [CommonModule, ReactiveFormsModule, RouterModule],
  template: `
    <div class="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100 flex items-center justify-center p-4">
      <div class="bg-white rounded-2xl shadow-2xl w-full max-w-md p-8">
        <!-- Logo -->
        <div class="flex justify-center mb-6">
          <div class="flex items-center gap-2">
            <div class="w-12 h-12 bg-gradient-to-br from-blue-600 to-indigo-700 rounded-lg flex items-center justify-center shadow-lg">
              <span class="text-white font-bold text-2xl">AC</span>
            </div>
            <div class="flex flex-col">
              <span class="font-bold text-gray-800 text-xl">Advance</span>
              <span class="text-sm text-gray-500">Company</span>
            </div>
          </div>
        </div>

        <!-- Success State -->
        <div *ngIf="emailSent" class="text-center">
          <div class="mb-6">
            <span class="material-icons text-green-600 text-6xl">mark_email_read</span>
          </div>
          <h2 class="text-2xl font-bold text-gray-800 mb-2">Email Sent!</h2>
          <p class="text-gray-600 mb-4">
            We've sent a password reset link to <strong>{{ forgotPasswordForm.get('email')?.value }}</strong>.
            Please check your inbox and follow the instructions.
          </p>
          <button
            type="button"
            (click)="resetForm()"
            class="w-full mt-2 text-blue-600 hover:text-blue-700 font-medium py-2">
            Send another email
          </button>
          <a routerLink="/auth/login"
             class="inline-block text-gray-500 hover:text-gray-700 text-sm mt-3">
            Back to Login
          </a>
        </div>

        <!-- Form State -->
        <div *ngIf="!emailSent">
          <h2 class="text-3xl font-bold text-gray-800 text-center mb-2">Forgot Password?</h2>
          <p class="text-gray-500 text-center mb-6">
            No worries! Enter your email and we'll send you a reset link.
          </p>

          <form [formGroup]="forgotPasswordForm" (ngSubmit)="onSubmit()" class="space-y-4" data-cy="forgot-password-form">
            <!-- Email Field -->
            <div>
              <label class="block text-sm font-medium text-gray-700 mb-1">Email Address</label>
              <input
                type="email"
                formControlName="email"
                data-cy="email-input"
                class="w-full px-4 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                [class.border-red-500]="forgotPasswordForm.get('email')?.invalid && forgotPasswordForm.get('email')?.touched"
                placeholder="Enter your email">
              <p *ngIf="forgotPasswordForm.get('email')?.invalid && forgotPasswordForm.get('email')?.touched"
                 class="text-red-500 text-sm mt-1">
                Please enter a valid email address
              </p>
            </div>

            <!-- Submit Button -->
            <button
              type="submit"
              data-cy="send-reset-btn"
              [disabled]="isLoading || forgotPasswordForm.invalid"
              class="w-full bg-gradient-to-r from-blue-600 to-indigo-600 text-white py-3 rounded-lg font-semibold hover:shadow-lg transition-all disabled:opacity-50 disabled:cursor-not-allowed">
              <span *ngIf="!isLoading">Send Reset Link</span>
              <span *ngIf="isLoading" class="flex items-center justify-center gap-2">
                <svg class="animate-spin h-5 w-5" viewBox="0 0 24 24">
                  <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4" fill="none"></circle>
                  <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                </svg>
                Sending...
              </span>
            </button>

            <!-- Back to Login -->
            <p class="text-center text-sm text-gray-600 mt-4">
              Remember your password?
              <a routerLink="/auth/login" data-cy="back-to-login" class="text-blue-600 hover:text-blue-700 font-medium">
                Sign in here
              </a>
            </p>
          </form>
        </div>
      </div>
    </div>
  `
})
export class ForgotPasswordComponent {
  private fb = inject(FormBuilder);
  private authService = inject(AuthService);
  private notificationService = inject(NotificationService);

  forgotPasswordForm: FormGroup;
  isLoading = false;
  emailSent = false;

  constructor() {
    this.forgotPasswordForm = this.fb.group({
      email: ['', [Validators.required, Validators.email]]
    });
  }

  resetForm(): void {
    this.emailSent = false;
    this.forgotPasswordForm.reset();
  }

  onSubmit(): void {
    if (this.forgotPasswordForm.invalid) {
      this.forgotPasswordForm.get('email')?.markAsTouched();
      return;
    }

    this.isLoading = true;
    const email = this.forgotPasswordForm.get('email')?.value;

    this.authService.forgotPassword(email).subscribe({
      next: () => {
        this.emailSent = true;
        this.isLoading = false;
        // Note: Backend returns success even if email doesn't exist (security)
      },
      error: () => {
        this.isLoading = false;
        this.notificationService.error('Failed to send reset link. Please try again.');
      }
    });
  }
}