import { Component, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import {
  FormBuilder,
  FormGroup,
  Validators,
  ReactiveFormsModule,
  AbstractControl,
  ValidationErrors
} from '@angular/forms';
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

  selectedPhoto: File | null = null;
  photoPreview: string | null = null;

  constructor() {
    this.registerForm = this.fb.group({
      full_name: ['', [Validators.required, Validators.minLength(2)]],
      email: ['', [Validators.required, Validators.email]],
      phone_number: ['', [Validators.required, Validators.pattern(/^\+?[0-9]{10,15}$/)]],
      password: [
        '',
        [
          Validators.required,
          Validators.minLength(12),
          this.passwordComplexityValidator
        ]
      ],
      password_confirm: ['', Validators.required]
    }, { validators: this.passwordMatchValidator });
  }

  // ---------------- VALIDATORS ----------------
  passwordComplexityValidator(control: AbstractControl): ValidationErrors | null {
    const value = control.value;
    if (!value) return null;

    const errors: ValidationErrors = {};
    if (!/[A-Z]/.test(value)) errors['noUpperCase'] = true;
    if (!/[a-z]/.test(value)) errors['noLowerCase'] = true;
    if (!/[0-9]/.test(value)) errors['noNumeric'] = true;
    if (!/[!@#$%^&*()_+\-=[\]{};':"\\|,.<>/?]/.test(value)) errors['noSpecialChar'] = true;
    if (/^\d+$/.test(value)) errors['allNumeric'] = true;

    return Object.keys(errors).length ? errors : null;
  }

  passwordMatchValidator(form: FormGroup) {
    const password = form.get('password');
    const confirm = form.get('password_confirm');
    if (password?.value !== confirm?.value) {
      confirm?.setErrors({ mismatch: true });
      return { mismatch: true };
    }
    return null;
  }

  // ---------------- PHOTO ----------------
  onPhotoSelected(event: Event) {
    const input = event.target as HTMLInputElement;
    const file = input.files?.[0];
    if (!file) return;

    if (!file.type.startsWith('image/')) {
      this.notificationService.error('Please select an image file');
      return;
    }
    if (file.size > 5 * 1024 * 1024) {
      this.notificationService.error('Image size should be less than 5MB');
      return;
    }

    this.selectedPhoto = file;
    const reader = new FileReader();
    reader.onload = () => (this.photoPreview = reader.result as string);
    reader.readAsDataURL(file);
  }

  clearPhotoSelection(input: HTMLInputElement) {
    this.selectedPhoto = null;
    this.photoPreview = null;
    input.value = '';
  }

  // ---------------- SUBMIT ----------------
  onSubmit(): void {
    if (this.registerForm.invalid) {
      this.registerForm.markAllAsTouched();
      return;
    }

    this.isLoading = true;

    const payload = this.selectedPhoto
      ? this.buildFormData()
      : this.buildJsonPayload();

    this.authService.register(payload as any).subscribe({
      next: (response: any) => {
        this.isLoading = false;

        // Backend response shape:
        // { success, message, toast_type, data: { user, tokens } }

        // Show backend message e.g. "Registration successful! Please check your email..."
        const message = response?.message ??
          'Registration successful! Please verify your email to continue. 🎉';

        const toastType = response?.toast_type || 'success';
        if (toastType === 'success') this.notificationService.success(message);
        else if (toastType === 'info') this.notificationService.info(message);
        else if (toastType === 'warning') this.notificationService.warning(message);
        else this.notificationService.success(message);

        // Redirect to verify-email page with email pre-filled
        const email = this.registerForm.get('email')?.value;
        this.router.navigate(['/auth/verify-email'], {
          queryParams: { email }
        });
      },
      error: (err: any) => {
        this.isLoading = false;

        // Backend error shape:
        // { success: false, message, toast_type: "error", errors: {...} }
        const toastMessage = err?.error?.message ??
                             'Registration failed. Please try again.';
        this.notificationService.error(toastMessage);

        // Apply field-level errors from backend if present
        if (err?.error?.errors) {
          this.applyBackendErrors(err.error.errors);
        }
      }
    });
  }

  // ---------------- PAYLOAD BUILDERS ----------------
  private buildJsonPayload() {
    return this.registerForm.value;
  }

  private buildFormData(): FormData {
    const formData = new FormData();
    Object.entries(this.registerForm.value).forEach(([key, value]) => {
      if (value !== null && value !== undefined) formData.append(key, String(value));
    });
    if (this.selectedPhoto) formData.append('profile_photo', this.selectedPhoto);
    return formData;
  }

  // ---------------- BACKEND ERROR MAPPING ----------------
  private applyBackendErrors(errors: Record<string, string[]>) {
    Object.entries(errors).forEach(([field, messages]) => {
      const control = this.registerForm.get(field);
      if (control) {
        control.setErrors({ backend: messages.join(' | ') });
        control.markAsTouched();
      }
    });
  }

  // ---------------- ERROR DISPLAY ----------------
  getErrorMessage(fieldName: string): string {
    const control = this.registerForm.get(fieldName);
    if (!control || !control.errors) return '';

    if (control.hasError('backend')) return control.errors['backend'];
    if (control.hasError('required')) return `${this.getLabel(fieldName)} is required`;
    if (control.hasError('email')) return 'Enter a valid email';
    if (control.hasError('pattern')) return 'Enter a valid phone number';
    if (control.hasError('minlength'))
      return `Minimum ${control.errors['minlength'].requiredLength} characters`;
    if (control.hasError('mismatch')) return 'Passwords do not match';
    if (control.hasError('noUpperCase')) return 'Must contain an uppercase letter';
    if (control.hasError('noLowerCase')) return 'Must contain a lowercase letter';
    if (control.hasError('noNumeric')) return 'Must contain a number';
    if (control.hasError('noSpecialChar')) return 'Must contain a special character';
    if (control.hasError('allNumeric')) return 'Password cannot be all numbers';

    return '';
  }

  private getLabel(field: string): string {
    const map: Record<string, string> = {
      full_name: 'Full name',
      email: 'Email',
      phone_number: 'Phone number',
      password: 'Password',
      password_confirm: 'Password confirmation'
    };
    return map[field] || field;
  }

  togglePassword() { this.showPassword = !this.showPassword; }
  toggleConfirmPassword() { this.showConfirmPassword = !this.showConfirmPassword; }

  // ---------------- PASSWORD REQUIREMENTS ----------------
  passwordHasUpperCase(): boolean {
    return /[A-Z]/.test(this.registerForm.get('password')?.value || '');
  }

  passwordHasLowerCase(): boolean {
    return /[a-z]/.test(this.registerForm.get('password')?.value || '');
  }

  passwordHasNumber(): boolean {
    return /[0-9]/.test(this.registerForm.get('password')?.value || '');
  }

  passwordHasSpecialChar(): boolean {
    return /[!@#$%^&*()_+\-=[\]{};':"\\|,.<>/?]/.test(
      this.registerForm.get('password')?.value || ''
    );
  }

  passwordMinLength(): boolean {
    return (this.registerForm.get('password')?.value || '').length >= 12;
  }
}