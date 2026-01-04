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
  
  account: FinancialAccount | null = null;
  deposits: Deposit[] = [];
  depositForm: FormGroup;

  constructor() {
    this.depositForm = this.fb.group({
      amount: ['', [Validators.required, Validators.min(100)]],
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
  }

  loadFinancialData() {
    this.financialService.getMyAccount().subscribe({
      next: (account) => {
        this.account = account;
      },
      error: (error) => {
        console.error('Error loading account:', error);
      }
    });

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

  toggleSidebar() {
    this.sidebarOpen = !this.sidebarOpen;
  }

  toggleDepositForm() {
    this.showDepositForm = !this.showDepositForm;
    if (!this.showDepositForm) {
      this.depositForm.reset({ payment_method: 'mpesa' });
    }
  }

  onSubmitDeposit() {
    if (this.depositForm.valid) {
      this.isSubmitting = true;
      
      this.financialService.createDeposit(this.depositForm.value).subscribe({
        next: (deposit) => {
          this.notificationService.success('Deposit initiated successfully!');
          this.deposits.unshift(deposit);
          this.toggleDepositForm();
          this.isSubmitting = false;
        },
        error: (error) => {
          this.notificationService.error('Failed to initiate deposit');
          this.isSubmitting = false;
        }
      });
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
}