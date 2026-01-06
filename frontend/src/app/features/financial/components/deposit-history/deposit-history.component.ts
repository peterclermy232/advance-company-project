import { Component, inject, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormBuilder, FormGroup, ReactiveFormsModule, Validators } from '@angular/forms';
import { SidebarComponent } from '../../../../shared/components/sidebar/sidebar.component';
import { HeaderComponent } from '../../../../shared/components/header/header.component';
import { LoadingComponent } from '../../../../shared/components/loading/loading.component';
import { CurrencyFormatPipe } from '../../../../shared/pipes/currency-format.pipe';
import { FinancialService } from '../../../../core/services/financial.service';
import { NotificationService } from '../../../../core/services/notification.service';
import { Deposit } from '../../../../core/models/financial.model';

@Component({
  selector: 'app-deposit-history',
  standalone: true,
  imports: [
    CommonModule,
    ReactiveFormsModule,
    HeaderComponent,
    SidebarComponent,
    LoadingComponent,
    CurrencyFormatPipe
  ],
  templateUrl: './deposit-history.component.html',
  styleUrls: ['./deposit-history.component.scss']
})
export class DepositHistoryComponent implements OnInit {
  private fb = inject(FormBuilder);
  private financialService = inject(FinancialService);
  private notificationService = inject(NotificationService);

  sidebarOpen = true;
  isLoading = true;
  isProcessing = false;
  showApproveModal = false;
  showRejectModal = false;
  filterStatus: 'pending' | 'completed' | 'failed' = 'pending';
  
  selectedDeposit: Deposit | null = null;
  allDeposits: Deposit[] = [];
  
  rejectForm: FormGroup;

  constructor() {
    this.rejectForm = this.fb.group({
      reason: ['', Validators.required]
    });
  }

  ngOnInit() {
    this.loadDeposits();
  }

  get pendingDeposits() {
    return this.allDeposits.filter(d => d.status === 'pending');
  }

  get approvedDeposits() {
    return this.allDeposits.filter(d => d.status === 'completed');
  }

  get rejectedDeposits() {
    return this.allDeposits.filter(d => d.status === 'failed');
  }

  get filteredDeposits() {
    return this.allDeposits.filter(d => d.status === this.filterStatus);
  }

  loadDeposits() {
    this.financialService.getDeposits().subscribe({
      next: (response) => {
        this.allDeposits = response.results;
        this.isLoading = false;
      },
      error: (error) => {
        console.error('Error loading deposits:', error);
        this.notificationService.error('Failed to load deposits');
        this.isLoading = false;
      }
    });
  }

  toggleSidebar() {
    this.sidebarOpen = !this.sidebarOpen;
  }

  openApproveModal(deposit: Deposit) {
    this.selectedDeposit = deposit;
    this.showApproveModal = true;
  }

  openRejectModal(deposit: Deposit) {
    this.selectedDeposit = deposit;
    this.showRejectModal = true;
    this.rejectForm.reset();
  }

  closeModals() {
    this.showApproveModal = false;
    this.showRejectModal = false;
    this.selectedDeposit = null;
    this.rejectForm.reset();
  }

  confirmApprove() {
    if (!this.selectedDeposit) return;

    this.isProcessing = true;
    this.financialService.approveDeposit(this.selectedDeposit.id).subscribe({
      next: (response) => {
        this.notificationService.success('Deposit approved successfully');
        this.loadDeposits();
        this.closeModals();
        this.isProcessing = false;
      },
      error: (error) => {
        const message = error.error?.error || 'Failed to approve deposit';
        this.notificationService.error(message);
        this.isProcessing = false;
      }
    });
  }

  confirmReject() {
    if (!this.selectedDeposit || this.rejectForm.invalid) return;

    this.isProcessing = true;
    const reason = this.rejectForm.get('reason')?.value;

    this.financialService.rejectDeposit(this.selectedDeposit.id, reason).subscribe({
      next: (response) => {
        this.notificationService.success('Deposit rejected');
        this.loadDeposits();
        this.closeModals();
        this.isProcessing = false;
      },
      error: (error) => {
        const message = error.error?.error || 'Failed to reject deposit';
        this.notificationService.error(message);
        this.isProcessing = false;
      }
    });
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