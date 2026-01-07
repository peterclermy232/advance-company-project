import { Component, inject, EventEmitter, Output, Input } from '@angular/core';
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
    CommonModule, ReactiveFormsModule,
    HeaderComponent, 
        SidebarComponent, 
     CurrencyFormatPipe,
     LoadingComponent,
    ],
  templateUrl: './deposit-form.component.html',
  styleUrls: ['./deposit-form.component.scss']
})
export class DepositFormComponent {
  private fb = inject(FormBuilder);
  private financialService = inject(FinancialService);
  private toastService = inject(ToastService);

  @Input() canDeposit = true;
  @Output() depositCreated = new EventEmitter<void>();
  @Output() formCancelled = new EventEmitter<void>();

  readonly MONTHLY_DEPOSIT_AMOUNT = 20000;
  isSubmitting = false;
  depositForm: FormGroup;

  isLoading = true;
  sidebarOpen = true;

  constructor() {
    this.depositForm = this.fb.group({
      amount: [{ value: this.MONTHLY_DEPOSIT_AMOUNT, disabled: true }],
      payment_method: ['mpesa', Validators.required],
      mpesa_phone: [''],
      notes: ['']
    });

    this.depositForm.get('payment_method')?.valueChanges.subscribe(method => {
      const phoneControl = this.depositForm.get('mpesa_phone');
      if (method === 'mpesa') {
        phoneControl?.setValidators([Validators.required, Validators.pattern(/^\+?[0-9]{10,15}$/)]);
      } else {
        phoneControl?.clearValidators();
      }
      phoneControl?.updateValueAndValidity();
    });
  }

  onSubmit() {
    if (this.depositForm.valid && this.canDeposit) {
      this.isSubmitting = true;
      
      const formData = {
        ...this.depositForm.getRawValue(),
        amount: this.MONTHLY_DEPOSIT_AMOUNT
      };

      this.financialService.createDeposit(formData).subscribe({
        next: (deposit) => {
          this.toastService.success(
            'Monthly deposit of KES 20,000 initiated successfully! Please complete the payment process.'
          );
          this.isSubmitting = false;
          this.depositForm.reset({ 
            amount: this.MONTHLY_DEPOSIT_AMOUNT,
            payment_method: 'mpesa' 
          });
          this.depositCreated.emit();
        },
        error: (error) => {
          const errorMessage = error.error?.amount?.[0] || 
                             error.error?.non_field_errors?.[0] ||
                             'Failed to initiate deposit';
          this.toastService.error(errorMessage);
          this.isSubmitting = false;
        }
      });
    } else if (!this.canDeposit) {
      this.toastService.warning('You have already paid this month');
    } else {
      Object.keys(this.depositForm.controls).forEach(key => {
        this.depositForm.get(key)?.markAsTouched();
      });
    }
  }
  toggleSidebar() {
    this.sidebarOpen = !this.sidebarOpen;
  }
}