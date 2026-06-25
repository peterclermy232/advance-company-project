import { Component, inject, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { HeaderComponent } from '../../shared/components/header/header.component';
import { SidebarComponent } from '../../shared/components/sidebar/sidebar.component';
import { LoadingComponent } from '../../shared/components/loading/loading.component';
import { DepositTableComponent } from './components/deposit-table/deposit-table.component';
import { DepositApprovalModalComponent } from './components/deposit-approval-modal/deposit-approval-modal.component';
import { DepositRejectionModalComponent } from './components/deposit-rejection-modal/deposit-rejection-modal.component';
import { FinancialService } from '../../core/services/financial.service';
import { AuthService } from '../../core/services/auth.service';
import { Deposit } from '../../core/models/financial.model';
import { ToastService } from '../../core/services/toast.service';

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
  private authService = inject(AuthService);
  private notificationService = inject(ToastService);

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

  get isAdmin(): boolean {
    return this.authService.isAdmin();
  }

  get pendingDeposits() {
    // Include both 'pending' and 'processing' statuses
    return (this.allDeposits || []).filter(d => 
      d.status === 'pending' || d.status === 'processing'
    );
  }

  get approvedDeposits() {
    return (this.allDeposits || []).filter(d => d.status === 'completed');
  }

  get rejectedDeposits() {
    return (this.allDeposits || []).filter(d => d.status === 'failed');
  }

  get filteredDeposits() {
    if (this.filterStatus === 'pending') {
      // Show both pending and processing when "pending" tab is selected
      return (this.allDeposits || []).filter(d => 
        d.status === 'pending' || d.status === 'processing'
      );
    }
    return (this.allDeposits || []).filter(d => d.status === this.filterStatus);
  }

  loadDeposits() {
    this.isLoading = true;
    this.financialService.getDeposits().subscribe({
      next: (response) => {
        // Handle both array response and paginated response with results
        if (Array.isArray(response)) {
          this.allDeposits = response;
        } else if (response && response.results) {
          this.allDeposits = response.results;
        } else {
          this.allDeposits = [];
        }
        this.isLoading = false;
      },
      error: (error) => {
        console.error('Error loading deposits:', error);
        this.notificationService.error('Failed to load deposits');
        this.allDeposits = [];
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
    if (!this.isAdmin) {
      this.notificationService.error('Only admins can approve deposits');
      return;
    }
    this.selectedDeposit = deposit;
    this.showApproveModal = true;
  }

  handleReject(deposit: Deposit) {
    if (!this.isAdmin) {
      this.notificationService.error('Only admins can reject deposits');
      return;
    }
    this.selectedDeposit = deposit;
    this.showRejectModal = true;
  }

  confirmApprove() {
    if (!this.selectedDeposit || !this.isAdmin) return;

    this.isProcessing = true;
    const loadingToast = this.notificationService.loading('Processing approval...');
    
    this.financialService.approveDeposit(this.selectedDeposit.uuid).subscribe({
      next: () => {
        loadingToast.dismiss();
        this.notificationService.success(`✓ Deposit of ${this.selectedDeposit!.amount} approved for ${this.selectedDeposit!.user_name}!`);
        this.loadDeposits();
        this.closeModals();
        this.isProcessing = false;
      },
      error: (error) => {
        loadingToast.dismiss();
        const message = error.error?.error || 'Failed to approve deposit';
        this.notificationService.error(message);
        this.isProcessing = false;
      }
    });
  }

  confirmReject(reason: string) {
    if (!this.selectedDeposit || !this.isAdmin) return;

    this.isProcessing = true;
    const loadingToast = this.notificationService.loading('Processing rejection...');
    
    this.financialService.rejectDeposit(this.selectedDeposit.uuid, reason).subscribe({
      next: () => {
        loadingToast.dismiss();
        this.notificationService.warning(`⚠️ Deposit rejected for ${this.selectedDeposit!.user_name}`);
        this.loadDeposits();
        this.closeModals();
        this.isProcessing = false;
      },
      error: (error) => {
        loadingToast.dismiss();
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