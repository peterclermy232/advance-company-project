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
    console.log('LoginComponent initialized');
    console.log('ToastService available:', !!this.toastService);
    
    this.loginForm = this.fb.group({
      email: ['', [Validators.required, Validators.email]],
      password: ['', [Validators.required, Validators.minLength(6)]],
      remember: [false]
    });

    // Test toast on page load (1 second delay)
    // setTimeout(() => {
    //   console.log('Testing toast on page load...');
    //   this.toastService.info('Login page loaded successfully! 🎉');
    // }, 1000);
  }

  onSubmit(): void {
    console.log('Login form submitted');
    console.log('Form valid:', this.loginForm.valid);

    // Validate form
    if (this.loginForm.invalid) {
      console.log('Form is invalid, marking fields as touched');
      Object.keys(this.loginForm.controls).forEach(key => {
        this.loginForm.get(key)?.markAsTouched();
      });
      
      // Show warning toast for client-side validation
      this.toastService.warning('Please fill in all required fields correctly');
      return;
    }

    this.isLoading = true;

    const credentials = {
      email: this.loginForm.get('email')?.value,
      password: this.loginForm.get('password')?.value
    };

    console.log('Sending login request...');
    this.authService.login(credentials).subscribe({
      next: (response: any) => {
        console.log('Login response received:', response);
        this.isLoading = false;
        
        // Check if 2FA is required
        if (response?.requires_2fa) {
          console.log('2FA required, showing modal');
          this.show2FAModal = true;
          // Toast is shown by AuthService.showBackendToast()
        } else {
          console.log('Login successful, navigating to dashboard...');
          // Toast is shown by AuthService.showBackendToast()
          // Navigate after a short delay to show the toast
          setTimeout(() => {
            this.router.navigate(['/dashboard']);
          }, 600);
        }
      },
      error: (error) => {
        // console.error('Login error:', error);
        // console.error('Error status:', error.status);
        // console.error('Error response:', error.error);
        
        // Toast is shown by AuthService.handleBackendError()
        this.isLoading = false;
      }
    });
  }

  verify2FA(isBackupCode = false): void {
    console.log('Verifying 2FA code...');
    
    // Validate 2FA code
    if (!this.twoFactorCode || this.twoFactorCode.trim().length === 0) {
      console.log('2FA code is empty');
      this.toastService.warning('Please enter a verification code');
      return;
    }

    this.isLoading = true;
    
    this.authService.verify2FA(this.twoFactorCode, isBackupCode).subscribe({
      next: () => {
        console.log('2FA verification successful');
        this.isLoading = false;
        this.show2FAModal = false;
        
        // Toast is shown by AuthService.showBackendToast()
        // Navigate after showing toast
        setTimeout(() => {
          this.router.navigate(['/dashboard']);
        }, 600);
      },
      error: (error) => {
        console.error('2FA verification error:', error);
        
        // Toast is shown by AuthService.handleBackendError()
        this.isLoading = false;
      }
    });
  }

  cancel2FA(): void {
    console.log('2FA cancelled');
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