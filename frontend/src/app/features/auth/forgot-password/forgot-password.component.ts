import { Component, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormBuilder, FormGroup, Validators, ReactiveFormsModule } from '@angular/forms';
import { Router, RouterModule } from '@angular/router';
import { HttpClient } from '@angular/common/http';
import { environment } from '../../../environments/environment';
import { NotificationService } from '../../../core/services/notification.service';

@Component({
  selector: 'app-forgot-password',
  standalone: true,
  imports: [CommonModule, ReactiveFormsModule, RouterModule],
  templateUrl: './forgot-password.component.html',
  styleUrls: ['./forgot-password.component.scss']
})
export class ForgotPasswordComponent {
  private fb = inject(FormBuilder);
  private http = inject(HttpClient);
  private router = inject(Router);
  private notificationService = inject(NotificationService);

  forgotPasswordForm: FormGroup;
  isLoading = false;
  emailSent = false;

  constructor() {
    this.forgotPasswordForm = this.fb.group({
      email: ['', [Validators.required, Validators.email]]
    });
  }

  onSubmit(): void {
    if (this.forgotPasswordForm.invalid) return;

    this.isLoading = true;

    this.http.post(`${environment.apiUrl}/auth/users/forgot_password/`, this.forgotPasswordForm.value)
      .subscribe({
        next: () => {
          this.emailSent = true;
          this.isLoading = false;
          this.notificationService.success('Password reset email sent!');
        },
        error: (error) => {
          this.isLoading = false;
          if (error.status === 429) {
            this.notificationService.error('Too many attempts. Please try again later.');
          } else {
            this.notificationService.error('Failed to send reset email. Please try again.');
          }
        }
      });
  }

  resetForm(): void {
    this.emailSent = false;
    this.forgotPasswordForm.reset();
  }
}