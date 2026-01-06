import { Component, inject, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormBuilder, FormGroup, Validators, ReactiveFormsModule } from '@angular/forms';
import { HeaderComponent } from '../../shared/components/header/header.component';
import { SidebarComponent } from '../../shared/components/sidebar/sidebar.component';
import { LoadingComponent } from '../../shared/components/loading/loading.component';
import { CurrencyFormatPipe } from '../../shared/pipes/currency-format.pipe';
import { FinancialService } from '../../core/services/financial.service';
import { NotificationService } from '../../core/services/notification.service';
import { FinancialAccount, Deposit } from '../../core/models/financial.model';

@Component({
  selector: 'app-financial',
  standalone: true,
  imports: [
    CommonModule, 
    ReactiveFormsModule, 
    HeaderComponent, 
    SidebarComponent, 
    LoadingComponent,
    CurrencyFormatPipe
  ],
  templateUrl: './financial.component.html',
  styleUrls: ['./financial.component.scss']
})
export class FinancialComponent implements OnInit {
  private fb = inject(FormBuilder);
  private financialService = inject(FinancialService);
  private notificationService = inject(NotificationService);

  sidebarOpen = true;
  isLoading = true;
  isSubmitting = false;
  showDepositForm = false;
  canDeposit = true;
  
  // Fixed monthly deposit amount
  readonly MONTHLY_DEPOSIT_AMOUNT = 20000;
  
  account: FinancialAccount | null = null;
  deposits: Deposit[] = [];
  depositForm: FormGroup;
  monthlyDeposits = 0;
  hasPaidThisMonth = false;

  constructor() {
    this.depositForm = this.fb.group({
      amount: [{ value: this.MONTHLY_DEPOSIT_AMOUNT, disabled: true }], // Amount is fixed and disabled
      payment_method: ['mpesa', Validators.required],
      mpesa_phone: [''],
      notes: ['']
    });

    // Add phone validation when M-Pesa is selected
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

  ngOnInit() {
    this.loadFinancialData();
    this.checkCanDeposit();
  }

  loadFinancialData() {
    // Load account with monthly deposit info
    this.financialService.getMyAccount().subscribe({
      next: (account: any) => {
        this.account = account;
        this.monthlyDeposits = parseFloat(account.monthly_deposits || '0');
        this.hasPaidThisMonth = account.has_paid_this_month || false;
      },
      error: (error) => {
        console.error('Error loading account:', error);
        this.notificationService.error('Failed to load account information');
      }
    });

    // Load deposit history
    this.financialService.getDeposits().subscribe({
      next: (response) => {
        this.deposits = response.results;
        this.isLoading = false;
      },
      error: (error) => {
        console.error('Error loading deposits:', error);
        this.isLoading = false;
      }
    });
  }

  checkCanDeposit() {
    this.financialService.canDeposit().subscribe({
      next: (response: any) => {
        this.canDeposit = response.can_deposit;
        if (!this.canDeposit) {
          this.notificationService.info('You have already made your monthly deposit of KES 20,000 for this month');
        }
      },
      error: (error) => {
        console.error('Error checking deposit eligibility:', error);
      }
    });
  }

  toggleSidebar() {
    this.sidebarOpen = !this.sidebarOpen;
  }

  toggleDepositForm() {
    if (!this.canDeposit) {
      this.notificationService.warning('You have already paid this month. Only one deposit of KES 20,000 per month is allowed.');
      return;
    }
    
    this.showDepositForm = !this.showDepositForm;
    if (!this.showDepositForm) {
      this.depositForm.reset({ 
        amount: this.MONTHLY_DEPOSIT_AMOUNT,
        payment_method: 'mpesa' 
      });
    }
  }

  onSubmitDeposit() {
    if (this.depositForm.valid && this.canDeposit) {
      this.isSubmitting = true;
      
      // Include the fixed amount in the payload
      const formData = {
        ...this.depositForm.getRawValue(), // getRawValue() includes disabled fields
        amount: this.MONTHLY_DEPOSIT_AMOUNT
      };

      this.financialService.createDeposit(formData).subscribe({
        next: (deposit) => {
          this.notificationService.success(
            'Monthly deposit of KES 20,000 initiated successfully! ' +
            'Please complete the payment process.'
          );
          this.deposits.unshift(deposit);
          this.toggleDepositForm();
          this.isSubmitting = false;
          
          // Reload financial data to update dashboard
          this.loadFinancialData();
          this.checkCanDeposit();
        },
        error: (error) => {
          const errorMessage = error.error?.amount?.[0] || 
                             error.error?.non_field_errors?.[0] ||
                             'Failed to initiate deposit';
          this.notificationService.error(errorMessage);
          this.isSubmitting = false;
        }
      });
    } else if (!this.canDeposit) {
      this.notificationService.warning('You have already paid this month');
    } else {
      Object.keys(this.depositForm.controls).forEach(key => {
        this.depositForm.get(key)?.markAsTouched();
      });
    }
  }

  getStatusClass(status: string): string {
    const classes: { [key: string]: string } = {
      'completed': 'bg-green-100 text-green-800',
      'pending': 'bg-yellow-100 text-yellow-800',
      'failed': 'bg-red-100 text-red-800',
      'cancelled': 'bg-gray-100 text-gray-800'
    };
    return classes[status] || 'bg-gray-100 text-gray-800';
  }

  getPaymentMethodLabel(method: string): string {
    const labels: { [key: string]: string } = {
      'mpesa': 'M-Pesa',
      'bank': 'Bank Transfer',
      'mansa_x': 'Mansa-X'
    };
    return labels[method] || method;
  }
}