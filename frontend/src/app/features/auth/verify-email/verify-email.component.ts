import { Component, inject, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ActivatedRoute, Router, RouterModule } from '@angular/router';
import { AuthService } from '../../../core/services/auth.service';
import { NotificationService } from '../../../core/services/notification.service';

@Component({
  selector: 'app-verify-email',
  standalone: true,
  imports: [CommonModule, RouterModule],
  templateUrl: './verify-email.component.html',
  styleUrls: ['./verify-email.component.scss']
})
export class VerifyEmailComponent implements OnInit {
  private authService = inject(AuthService);
  private route = inject(ActivatedRoute);
  private router = inject(Router);
  private notificationService = inject(NotificationService);

  isVerifying = true;
  verificationSuccess = false;
  errorMessage = '';
  isResending = false;

  email: string | null = null;
  token: string | null = null;

  ngOnInit(): void {
    // Get email and token from query params
    this.route.queryParams.subscribe(params => {
      this.email = params['email'];
      this.token = params['token'];

      if (this.email && this.token) {
        this.verifyEmail();
      } else {
        this.isVerifying = false;
        this.errorMessage = 'Invalid verification link. Email and token are required.';
      }
    });
  }

  verifyEmail(): void {
    if (!this.email || !this.token) return;

    this.isVerifying = true;

    this.authService.verifyEmail(this.email, this.token).subscribe({
      next: () => {
        this.verificationSuccess = true;
        this.isVerifying = false;
        this.notificationService.success('Email verified successfully! 🎉');
      },
      error: (error) => {
        this.verificationSuccess = false;
        this.isVerifying = false;
        this.errorMessage = error.error?.error || 
                          error.error?.detail || 
                          'Verification failed. The link may have expired.';
        this.notificationService.error(this.errorMessage);
      }
    });
  }

  resendVerification(): void {
    if (!this.email) {
      this.notificationService.error('Email address not found');
      return;
    }

    this.isResending = true;

    this.authService.resendVerification(this.email).subscribe({
      next: () => {
        this.isResending = false;
        this.notificationService.success('Verification email sent! Check your inbox. 📧');
      },
      error: () => {
        this.isResending = false;
        this.notificationService.error('Failed to resend email. Please try again.');
      }
    });
  }

  goToDashboard(): void {
    this.router.navigate(['/dashboard']);
  }

  goToLogin(): void {
    this.router.navigate(['/auth/login']);
  }
}