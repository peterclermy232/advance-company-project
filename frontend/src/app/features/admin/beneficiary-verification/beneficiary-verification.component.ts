import { Component, inject, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { HeaderComponent } from '../../../shared/components/header/header.component';
import { SidebarComponent } from '../../../shared/components/sidebar/sidebar.component';
import { LoadingComponent } from '../../../shared/components/loading/loading.component';
import { CurrencyFormatPipe } from '../../../shared/pipes/currency-format.pipe';
import { ApiService } from '../../../core/services/api.service';
import { ToastService } from '../../../core/services/toast.service';
import { AuthService } from '../../../core/services/auth.service';

interface Beneficiary {
  uuid: string;
  user_name: string;
  user_email: string;
  user_phone: string;
  name: string;
  relation: string;
  relation_display: string;
  age: number;
  gender: string;
  phone_number?: string;
  profession?: string;
  identity_document_url: string;
  birth_certificate_url?: string;
  death_certificate_url?: string;
  verification_status: string;
  verification_status_display: string;
  status: string;
  created_at: string;
}

interface BeneficiaryStatistics {
  total: number;
  pending: number;
  verified: number;
  rejected: number;
}

@Component({
  selector: 'app-beneficiary-verification',
  standalone: true,
  imports: [
    CommonModule,
    FormsModule,
    HeaderComponent,
    SidebarComponent,
    LoadingComponent,
    CurrencyFormatPipe
  ],
  templateUrl: './beneficiary-verification.component.html',
  styleUrls: ['./beneficiary-verification.component.scss']
})
export class BeneficiaryVerificationComponent implements OnInit {
  private apiService = inject(ApiService);
  private toastService = inject(ToastService);
  private authService = inject(AuthService);

  sidebarOpen = true;
  isLoading = true;
  isProcessing = false;

  beneficiaries: Beneficiary[] = [];
  statistics: BeneficiaryStatistics = {
    total: 0,
    pending: 0,
    verified: 0,
    rejected: 0
  };

  activeFilter: 'all' | 'pending' | 'verified' | 'rejected' = 'pending';
  
  filters = [
    { label: 'All', value: 'all' as const, count: 0 },
    { label: 'Pending', value: 'pending' as const, count: 0 },
    { label: 'Verified', value: 'verified' as const, count: 0 },
    { label: 'Rejected', value: 'rejected' as const, count: 0 }
  ];

  // Modal states
  showRejectModal = false;
  selectedBeneficiary: Beneficiary | null = null;
  rejectionReason = '';

  ngOnInit() {
    if (!this.authService.isAdmin()) {
      this.toastService.error('Access denied. Admin only.');
      return;
    }
    this.loadStatistics();
    this.loadBeneficiaries();
  }

  toggleSidebar() {
    this.sidebarOpen = !this.sidebarOpen;
  }

  loadStatistics() {
    this.apiService.get<BeneficiaryStatistics>('beneficiary/statistics/')
      .subscribe({
        next: (response) => {
          this.statistics = response;
          this.filters[0].count = response.total;
          this.filters[1].count = response.pending;
          this.filters[2].count = response.verified;
          this.filters[3].count = response.rejected;
        },
        error: (error) => {
          console.error('Error loading statistics:', error);
          this.toastService.error('Failed to load statistics');
        }
      });
  }

  loadBeneficiaries() {
    this.isLoading = true;
    const params: any = {};
    
    if (this.activeFilter !== 'all') {
      params.verification_status = this.activeFilter;
    }

    this.apiService.get<{ results: Beneficiary[] } | Beneficiary[]>('beneficiary/', params)
      .subscribe({
        next: (response) => {
          // Handle both paginated and array responses
          this.beneficiaries = Array.isArray(response) 
            ? response 
            : response.results || [];
          this.isLoading = false;
        },
        error: (error) => {
          console.error('Error loading beneficiaries:', error);
          this.toastService.error('Failed to load beneficiaries');
          this.beneficiaries = [];
          this.isLoading = false;
        }
      });
  }

  changeFilter(filter: 'all' | 'pending' | 'verified' | 'rejected') {
    this.activeFilter = filter;
    this.loadBeneficiaries();
  }

  verifyBeneficiary(beneficiary: Beneficiary) {
    if (!confirm(`Verify beneficiary ${beneficiary.name}?`)) {
      return;
    }

    this.isProcessing = true;
    const loadingToast = this.toastService.loading('Verifying beneficiary...');

    this.apiService.post(`beneficiary/${beneficiary.uuid}/verify/`, { 
      notes: 'Verified via admin panel' 
    }).subscribe({
      next: (response) => {
        loadingToast.dismiss();
        this.toastService.success(`✓ ${beneficiary.name} verified successfully!`);
        this.loadStatistics();
        this.loadBeneficiaries();
        this.isProcessing = false;
      },
      error: (error) => {
        loadingToast.dismiss();
        const message = error.error?.message || 'Failed to verify beneficiary';
        this.toastService.error(message);
        this.isProcessing = false;
      }
    });
  }

  openRejectModal(beneficiary: Beneficiary) {
    this.selectedBeneficiary = beneficiary;
    this.rejectionReason = '';
    this.showRejectModal = true;
  }

  closeRejectModal() {
    this.showRejectModal = false;
    this.selectedBeneficiary = null;
    this.rejectionReason = '';
  }

  confirmReject() {
    if (!this.selectedBeneficiary || !this.rejectionReason.trim()) {
      this.toastService.error('Please provide a reason for rejection');
      return;
    }

    this.isProcessing = true;
    const loadingToast = this.toastService.loading('Processing rejection...');

    this.apiService.post(`beneficiary/${this.selectedBeneficiary.uuid}/reject/`, { 
      reason: this.rejectionReason 
    }).subscribe({
      next: (response) => {
        loadingToast.dismiss();
        this.toastService.warning(` ${this.selectedBeneficiary!.name} rejected`);
        this.closeRejectModal();
        this.loadStatistics();
        this.loadBeneficiaries();
        this.isProcessing = false;
      },
      error: (error) => {
        loadingToast.dismiss();
        const message = error.error?.message || 'Failed to reject beneficiary';
        this.toastService.error(message);
        this.isProcessing = false;
      }
    });
  }

  viewDocument(url: string) {
    if (url) {
      window.open(url, '_blank');
    } else {
      this.toastService.error('Document URL not available');
    }
  }

  getStatusClass(status: string): string {
    const classes: { [key: string]: string } = {
      'pending': 'bg-yellow-100 text-yellow-800',
      'verified': 'bg-green-100 text-green-800',
      'rejected': 'bg-red-100 text-red-800'
    };
    return classes[status] || 'bg-gray-100 text-gray-800';
  }

  getGenderLabel(gender: string): string {
    const labels: { [key: string]: string } = {
      'M': 'Male',
      'F': 'Female',
      'O': 'Other'
    };
    return labels[gender] || gender;
  }
}