import { Component, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormBuilder, FormGroup, Validators, ReactiveFormsModule, AbstractControl, ValidationErrors } from '@angular/forms';
import { Router, RouterModule } from '@angular/router';
import { AuthService } from '../../../core/services/auth.service';
import { NotificationService } from '../../../core/services/notification.service';

@Component({
  selector: 'app-register',
  standalone: true,
  imports: [CommonModule, ReactiveFormsModule, RouterModule],
  templateUrl: './register.component.html',
  styleUrls: ['./register.component.scss']
})
export class RegisterComponent {
  private fb = inject(FormBuilder);
  private authService = inject(AuthService);
  private router = inject(Router);
  private notificationService = inject(NotificationService);

  registerForm: FormGroup;
  isLoading = false;
  showPassword = false;
  showConfirmPassword = false;
  
  // Photo upload properties
  selectedPhoto: File | null = null;
  photoPreview: string | null = null;

  constructor() {
    this.registerForm = this.fb.group({
      first_name: ['', [Validators.required, Validators.minLength(2)]],
      last_name: ['', [Validators.required, Validators.minLength(2)]],
      email: ['', [Validators.required, Validators.email]],
      phone_number: ['', [Validators.required, Validators.pattern(/^\+?[0-9]{10,15}$/)]],
      password: ['', [
        Validators.required,
        Validators.minLength(12),
        this.passwordComplexityValidator
      ]],
      password_confirm: ['', [Validators.required]]
    }, { validators: this.passwordMatchValidator });
  }

  // Custom validator for password complexity (matches Django backend)
  passwordComplexityValidator(control: AbstractControl): ValidationErrors | null {
    const value = control.value;
    
    if (!value) {
      return null;
    }

    const hasUpperCase = /[A-Z]/.test(value);
    const hasLowerCase = /[a-z]/.test(value);
    const hasNumeric = /[0-9]/.test(value);
    const hasSpecialChar = /[!@#$%^&*()_+\-=\[\]{};':"\\|,.<>\/?]/.test(value);
    const isNotAllNumeric = !/^\d+$/.test(value);

    const errors: ValidationErrors = {};

    if (!hasUpperCase) {
      errors['noUpperCase'] = true;
    }
    if (!hasLowerCase) {
      errors['noLowerCase'] = true;
    }
    if (!hasNumeric) {
      errors['noNumeric'] = true;
    }
    if (!hasSpecialChar) {
      errors['noSpecialChar'] = true;
    }
    if (!isNotAllNumeric) {
      errors['allNumeric'] = true;
    }

    return Object.keys(errors).length > 0 ? errors : null;
  }

  passwordMatchValidator(form: FormGroup) {
    const password = form.get('password');
    const confirmPassword = form.get('password_confirm');
    
    if (password?.value !== confirmPassword?.value) {
      confirmPassword?.setErrors({ mismatch: true });
      return { mismatch: true };
    }
    return null;
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
      
      this.notificationService.success('Photo selected successfully!');
    }
  }

  clearPhotoSelection(fileInput: HTMLInputElement) {
    this.selectedPhoto = null;
    this.photoPreview = null;
    fileInput.value = '';
    this.notificationService.info('Photo selection cleared');
  }

  onSubmit(): void {
    if (this.registerForm.invalid) {
      Object.keys(this.registerForm.controls).forEach(key => {
        this.registerForm.get(key)?.markAsTouched();
      });
      return;
    }

    this.isLoading = true;
    
    // Check if photo is included
    if (this.selectedPhoto) {
      // Use FormData for multipart upload with photo
      const formData = new FormData();
      
      // Append form fields (matching Django backend field names)
      formData.append('email', this.registerForm.get('email')?.value);
      formData.append('password', this.registerForm.get('password')?.value);
      formData.append('password_confirm', this.registerForm.get('password_confirm')?.value);
      formData.append('first_name', this.registerForm.get('first_name')?.value);
      formData.append('last_name', this.registerForm.get('last_name')?.value);
      formData.append('phone_number', this.registerForm.get('phone_number')?.value || '');
      
      // Append photo if selected
  if (this.selectedPhoto) {
    formData.append('profile_photo', this.selectedPhoto);
  }
      
      // Use registerWithPhoto method (you'll need to add this to AuthService)
      this.authService.register(formData as any).subscribe({
        next: (response) => {
          this.notificationService.success('Registration successful! 🎉');
          this.router.navigate(['/login']);
          this.isLoading = false;
        },
        error: (error) => {
          this.handleRegistrationError(error);
          this.isLoading = false;
        }
      });
    } else {
      // Use regular JSON payload without photo
      const payload = {
        email: this.registerForm.get('email')?.value,
        password: this.registerForm.get('password')?.value,
        password_confirm: this.registerForm.get('password_confirm')?.value,
        first_name: this.registerForm.get('first_name')?.value,
        last_name: this.registerForm.get('last_name')?.value,
        phone_number: this.registerForm.get('phone_number')?.value || ''
      };

      this.authService.register(payload).subscribe({
        next: (response) => {
          this.notificationService.success('Registration successful! 🎉');
          this.router.navigate(['/dashboard']);
          this.isLoading = false;
        },
        error: (error) => {
          this.handleRegistrationError(error);
          this.isLoading = false;
        }
      });
    }
  }

  private handleRegistrationError(error: any): void {
    // Handle backend password errors
    if (error.error?.password) {
      const passwordErrors = error.error.password;
      if (Array.isArray(passwordErrors)) {
        passwordErrors.forEach((err: string) => {
          this.notificationService.error(err);
        });
      } else {
        this.notificationService.error(passwordErrors);
      }
    } else if (error.error?.email) {
      const emailErrors = Array.isArray(error.error.email) 
        ? error.error.email[0] 
        : error.error.email;
      this.notificationService.error(emailErrors);
    } else if (error.error?.phone_number) {
      const phoneErrors = Array.isArray(error.error.phone_number)
        ? error.error.phone_number[0]
        : error.error.phone_number;
      this.notificationService.error(phoneErrors);
    } else if (error.error?.error) {
      this.notificationService.error(error.error.error);
    } else {
      this.notificationService.error('Registration failed. Please try again.');
    }
  }

  getErrorMessage(fieldName: string): string {
    const control = this.registerForm.get(fieldName);
    
    if (!control?.errors) {
      return '';
    }

    if (control.hasError('required')) {
      return `${this.getFieldDisplayName(fieldName)} is required`;
    }
    
    if (fieldName === 'email' && control.hasError('email')) {
      return 'Please enter a valid email';
    }
    
    if (fieldName === 'phone_number' && control.hasError('pattern')) {
      return 'Please enter a valid phone number (e.g., +254712345678)';
    }
    
    if (fieldName === 'password') {
      if (control.hasError('minlength')) {
        return 'Password must be at least 12 characters';
      }
      if (control.hasError('noUpperCase')) {
        return 'Password must contain at least one uppercase letter';
      }
      if (control.hasError('noLowerCase')) {
        return 'Password must contain at least one lowercase letter';
      }
      if (control.hasError('noNumeric')) {
        return 'Password must contain at least one number';
      }
      if (control.hasError('noSpecialChar')) {
        return 'Password must contain at least one special character';
      }
      if (control.hasError('allNumeric')) {
        return 'Password cannot be entirely numeric';
      }
    }
    
    if (fieldName === 'password_confirm' && control.hasError('mismatch')) {
      return 'Passwords do not match';
    }
    
    if (control.hasError('minlength')) {
      const minLength = control.errors?.['minlength'].requiredLength;
      return `Must be at least ${minLength} characters`;
    }
    
    return '';
  }

  private getFieldDisplayName(fieldName: string): string {
    const displayNames: { [key: string]: string } = {
      'first_name': 'First name',
      'last_name': 'Last name',
      'email': 'Email',
      'phone_number': 'Phone number',
      'password': 'Password',
      'password_confirm': 'Password confirmation'
    };
    return displayNames[fieldName] || fieldName;
  }

  togglePassword(): void {
    this.showPassword = !this.showPassword;
  }

  toggleConfirmPassword(): void {
    this.showConfirmPassword = !this.showConfirmPassword;
  }
}