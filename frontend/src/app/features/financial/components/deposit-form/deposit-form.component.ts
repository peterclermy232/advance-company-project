import { Component, inject, EventEmitter, Output, Input, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormBuilder, FormGroup, ReactiveFormsModule, Validators } from '@angular/forms';
import { CurrencyFormatPipe } from '../../../../shared/pipes/currency-format.pipe';
import { FinancialService } from '../../../../core/services/financial.service';
import { ToastService } from '../../../../core/services/toast.service';
import { HeaderComponent } from '../../../../shared/components/header/header.component';
import { SidebarComponent } from '../../../../shared/components/sidebar/sidebar.component';
import { LoadingComponent } from '../../../../shared/components/loading/loading.component';

@Component({
  selector: 'app-deposit-form',
  standalone: true,
  imports: [
    CommonModule, 
    ReactiveFormsModule,
    HeaderComponent, 
    SidebarComponent, 
    CurrencyFormatPipe,
    LoadingComponent,
  ],
  templateUrl: './deposit-form.component.html',
  styleUrls: ['./deposit-form.component.scss']
})
export class DepositFormComponent implements OnInit {
  private fb = inject(FormBuilder);
  private financialService = inject(FinancialService);
  private toastService = inject(ToastService);

  @Input() canDeposit = true;
  @Output() depositCreated = new EventEmitter<void>();
  @Output() formCancelled = new EventEmitter<void>();

  readonly MONTHLY_DEPOSIT_AMOUNT = 20000;
  isSubmitting = false;
  depositForm: FormGroup;
  showMpesaInstructions = false;
  mpesaCheckoutRequestId: string | null = null;

  isLoading = false;
  sidebarOpen = true;

  constructor() {
    this.depositForm = this.fb.group({
      amount: [{ value: this.MONTHLY_DEPOSIT_AMOUNT, disabled: true }],
      payment_method: ['mpesa', Validators.required],
      mpesa_phone: ['', [Validators.required, Validators.pattern(/^(\+?254|0)?[17]\d{8}$/)]],
      notes: ['']
    });

    // Update validators when payment method changes
    this.depositForm.get('payment_method')?.valueChanges.subscribe(method => {
      const phoneControl = this.depositForm.get('mpesa_phone');
      if (method === 'mpesa') {
        phoneControl?.setValidators([
          Validators.required, 
          Validators.pattern(/^(\+?254|0)?[17]\d{8}$/)
        ]);
        phoneControl?.enable();
      } else {
        phoneControl?.clearValidators();
        phoneControl?.disable();
      }
      phoneControl?.updateValueAndValidity();
    });
  }

  ngOnInit(): void {
    // Check if user can deposit this month
    this.checkDepositEligibility();
  }

  checkDepositEligibility(): void {
    this.financialService.canDeposit().subscribe({
      next: (response) => {
        this.canDeposit = response.can_deposit;
        if (!this.canDeposit) {
          this.toastService.warning(response.message);
        }
      },
      error: (error) => {
        console.error('Error checking deposit eligibility:', error);
      }
    });
  }

  formatPhoneNumber(phone: string): string {
    // Remove all non-digit characters
    let cleaned = phone.replace(/\D/g, '');
    
    // Convert to 254 format
    if (cleaned.startsWith('0')) {
      cleaned = '254' + cleaned.substring(1);
    } else if (cleaned.startsWith('254')) {
      // Already in correct format
    } else if (cleaned.startsWith('7') || cleaned.startsWith('1')) {
      cleaned = '254' + cleaned;
    }
    
    return cleaned;
  }

  onSubmit(): void {
    if (!this.canDeposit) {
      this.toastService.warning('You have already made a deposit this month');
      return;
    }

    if (this.depositForm.invalid) {
      Object.keys(this.depositForm.controls).forEach(key => {
        this.depositForm.get(key)?.markAsTouched();
      });
      this.toastService.error('Please fill in all required fields correctly');
      return;
    }

    this.isSubmitting = true;
    const paymentMethod = this.depositForm.get('payment_method')?.value;
    
    const formData: any = {
      payment_method: paymentMethod,
      notes: this.depositForm.get('notes')?.value || ''
    };

    // Add M-Pesa phone if payment method is M-Pesa
    if (paymentMethod === 'mpesa') {
      const rawPhone = this.depositForm.get('mpesa_phone')?.value;
      formData.mpesa_phone = this.formatPhoneNumber(rawPhone);
      
      // Show M-Pesa instructions
      this.showMpesaInstructions = true;
      this.toastService.info('Please check your phone for the M-Pesa prompt');
    }

    this.financialService.createDeposit(formData).subscribe({
      next: (deposit) => {
        console.log('Deposit created:', deposit);
        
        if (paymentMethod === 'mpesa') {
          // Store checkout request ID for tracking
          this.mpesaCheckoutRequestId = deposit.mpesa_checkout_request_id || null;
          
          // Show success message with M-Pesa instructions
          this.toastService.success(
            '🎉 M-Pesa STK Push sent! Check your phone and enter your PIN to complete the payment.',
            10000 // Show for 10 seconds
          );
          
          // Show detailed instructions
          setTimeout(() => {
            this.toastService.info(
              '📱 Enter your M-Pesa PIN on your phone to pay KES 20,000',
              8000
            );
          }, 1000);
        } else {
          this.toastService.success(
            `Deposit of KES 20,000 initiated successfully via ${paymentMethod}!`
          );
        }
        
        this.isSubmitting = false;
        this.canDeposit = false; // Prevent multiple deposits
        
        // Reset form but keep payment method
        this.depositForm.reset({ 
          amount: this.MONTHLY_DEPOSIT_AMOUNT,
          payment_method: 'mpesa' 
        });
        
        // Emit event to parent component
        this.depositCreated.emit();
        
        // Hide M-Pesa instructions after 15 seconds
        if (paymentMethod === 'mpesa') {
          setTimeout(() => {
            this.showMpesaInstructions = false;
          }, 15000);
        }
      },
      error: (error) => {
        console.error('Deposit error:', error);
        this.isSubmitting = false;
        this.showMpesaInstructions = false;
        
        // Handle specific error messages
        let errorMessage = 'Failed to initiate deposit';
        
        if (error.error?.error) {
          errorMessage = error.error.error;
        } else if (error.error?.details) {
          errorMessage = error.error.details;
        } else if (error.error?.mpesa_phone) {
          errorMessage = 'Invalid phone number format';
        } else if (error.error?.non_field_errors) {
          errorMessage = error.error.non_field_errors[0];
        }
        
        this.toastService.error(errorMessage);
      }
    });
  }

  cancelMpesaPayment(): void {
    this.showMpesaInstructions = false;
    this.mpesaCheckoutRequestId = null;
    this.isSubmitting = false;
  }

  toggleSidebar(): void {
    this.sidebarOpen = !this.sidebarOpen;
  }
}