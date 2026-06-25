import { Component, inject, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { RouterModule } from '@angular/router';
import { HeaderComponent } from '../../../shared/components/header/header.component';
import { SidebarComponent } from '../../../shared/components/sidebar/sidebar.component';
import { LoadingComponent } from '../../../shared/components/loading/loading.component';
import { BeneficiaryService } from '../../../core/services/beneficiary.service';
import { NotificationService } from '../../../core/services/notification.service';
import { Beneficiary } from '../../../core/models/beneficiary.model';

@Component({
  selector: 'app-beneficiary-list',
  standalone: true,
  imports: [CommonModule, FormsModule, RouterModule, HeaderComponent, SidebarComponent, LoadingComponent],
  templateUrl: './beneficiary-list.component.html',
  styleUrls: ['./beneficiary-list.component.scss']
})
export class BeneficiaryListComponent implements OnInit {
  private readonly beneficiaryService = inject(BeneficiaryService);
  private readonly notificationService = inject(NotificationService);

  sidebarOpen = true;
  isLoading = true;
  beneficiaries: Beneficiary[] = [];
  activeTab: 'active' | 'deceased' = 'active';

  // Remove modal
  selectedBeneficiary: Beneficiary | null = null;
  showDeleteModal = false;
  isDeleting = false;

  // Mark deceased modal
  showDeceasedModal = false;
  deceasedBeneficiary: Beneficiary | null = null;
  deceasedCertNumber = '';
  deceasedCertFile: File | null = null;
  isMarkingDeceased = false;

  ngOnInit() {
    this.loadBeneficiaries();
  }

  loadBeneficiaries() {
    this.isLoading = true;
    this.beneficiaryService.getBeneficiaries().subscribe({
      next: (response) => {
        this.beneficiaries = response.results ?? [];
        this.isLoading = false;
      },
      error: () => {
        this.notificationService.error('Failed to load beneficiaries');
        this.isLoading = false;
      }
    });
  }

  toggleSidebar() { this.sidebarOpen = !this.sidebarOpen; }

  // ── Computed lists ──────────────────────────────────────────────────────────

  get activeBeneficiaries(): Beneficiary[] {
    return this.beneficiaries.filter(b => b.status === 'active');
  }

  get deceasedBeneficiaries(): Beneficiary[] {
    return this.beneficiaries.filter(b => b.status === 'deceased');
  }

  get filteredBeneficiaries(): Beneficiary[] {
    return this.activeTab === 'active' ? this.activeBeneficiaries : this.deceasedBeneficiaries;
  }

  getTotalAllocation(): number {
    return this.activeBeneficiaries.reduce((sum, b) => sum + Number(b.percentage_allocation || 0), 0);
  }

  getVerifiedCount(): number {
    return this.activeBeneficiaries.filter(b => b.verification_status === 'verified').length;
  }

  getPendingCount(): number {
    return this.activeBeneficiaries.filter(b => b.verification_status === 'pending').length;
  }

  // ── Documents ───────────────────────────────────────────────────────────────

  openDocument(url: string | undefined) {
    if (url) window.open(url, '_blank');
  }

  // ── Remove ──────────────────────────────────────────────────────────────────

  confirmDelete(beneficiary: Beneficiary) {
    this.selectedBeneficiary = beneficiary;
    this.showDeleteModal = true;
  }

  deleteBeneficiary() {
    if (!this.selectedBeneficiary) return;
    this.isDeleting = true;
    this.beneficiaryService.deleteBeneficiary(this.selectedBeneficiary.uuid).subscribe({
      next: () => {
        this.beneficiaries = this.beneficiaries.filter(b => b.uuid !== this.selectedBeneficiary!.uuid);
        this.showDeleteModal = false;
        this.selectedBeneficiary = null;
        this.isDeleting = false;
      },
      error: () => { this.isDeleting = false; }
    });
  }

  // ── Mark deceased ───────────────────────────────────────────────────────────

  openMarkDeceased(beneficiary: Beneficiary) {
    this.deceasedBeneficiary = beneficiary;
    this.deceasedCertNumber = '';
    this.deceasedCertFile = null;
    this.showDeceasedModal = true;
  }

  closeDeceasedModal() {
    this.showDeceasedModal = false;
    this.deceasedBeneficiary = null;
    this.deceasedCertNumber = '';
    this.deceasedCertFile = null;
  }

  onDeceasedCertSelected(event: Event) {
    const input = event.target as HTMLInputElement;
    this.deceasedCertFile = input.files?.[0] ?? null;
  }

  confirmMarkDeceased() {
    if (!this.deceasedBeneficiary) return;
    this.isMarkingDeceased = true;

    const formData = new FormData();
    if (this.deceasedCertNumber) formData.append('death_certificate_number', this.deceasedCertNumber);
    if (this.deceasedCertFile) formData.append('death_certificate', this.deceasedCertFile);

    this.beneficiaryService.markDeceased(this.deceasedBeneficiary.uuid, formData).subscribe({
      next: () => {
        this.isMarkingDeceased = false;
        this.closeDeceasedModal();
        this.loadBeneficiaries();
      },
      error: () => { this.isMarkingDeceased = false; }
    });
  }

  // ── UI helpers ──────────────────────────────────────────────────────────────

  getVerificationBadgeClass(status: string): string {
    const map: Record<string, string> = {
      verified: 'bg-green-100 text-green-700 border border-green-200',
      pending:  'bg-yellow-100 text-yellow-700 border border-yellow-200',
      rejected: 'bg-red-100 text-red-700 border border-red-200',
    };
    return map[status] ?? 'bg-gray-100 text-gray-700';
  }

  getVerificationIcon(status: string): string {
    return ({ verified: '✓', pending: '⏳', rejected: '✗' } as Record<string, string>)[status] ?? '';
  }

  getRelationDisplay(b: Beneficiary): string {
    return b.relation_display ?? (b.relation.charAt(0).toUpperCase() + b.relation.slice(1));
  }

  getInitials(name: string): string {
    return name.split(' ').map(n => n[0]).join('').toUpperCase().slice(0, 2);
  }

  formatDate(dateStr: string): string {
    return new Date(dateStr).toLocaleDateString('en-KE', { day: 'numeric', month: 'short', year: 'numeric' });
  }
}
