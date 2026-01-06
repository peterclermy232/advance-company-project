import { Component, inject, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { HeaderComponent } from '../../shared/components/header/header.component';
import { SidebarComponent } from '../../shared/components/sidebar/sidebar.component';
import { LoadingComponent } from '../../shared/components/loading/loading.component';
import { DepositTableComponent } from './components/deposit-table/deposit-table.component';
import { DepositApprovalModalComponent } from './components/deposit-approval-modal/deposit-approval-modal.component';
import { DepositRejectionModalComponent } from './components/deposit-rejection-modal/deposit-rejection-modal.component';
import { FinancialService } from '../../core/services/financial.service';
import { NotificationService } from '../../core/services/notification.service';
import { Deposit } from '../../core/models/financial.model';

@Component({
  selector: 'app-financial',
  standalone: true,
  imports: [
    CommonModule,
    HeaderComponent,
    SidebarComponent,
    LoadingComponent,
    DepositTableComponent,
    DepositApprovalModalComponent,
    DepositRejectionModalComponent
  ],
  templateUrl: './financial.component.html',
  styleUrls: ['./financial.component.scss']
})
export class FinancialComponent implements OnInit {
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

  onFilterChange(status: 'pending' | 'completed' | 'failed') {
    this.filterStatus = status;
  }

  handleApprove(deposit: Deposit) {
    this.selectedDeposit = deposit;
    this.showApproveModal = true;
  }

  handleReject(deposit: Deposit) {
    this.selectedDeposit = deposit;
    this.showRejectModal = true;
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

  confirmReject(reason: string) {
    if (!this.selectedDeposit) return;

    this.isProcessing = true;
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

  closeModals() {
    this.showApproveModal = false;
    this.showRejectModal = false;
    this.selectedDeposit = null;
  }
}