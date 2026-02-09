import { Component, inject, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
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
  imports: [CommonModule, RouterModule, HeaderComponent, SidebarComponent, LoadingComponent],
  templateUrl: './beneficiary-list.component.html',
  styleUrls: ['./beneficiary-list.component.scss']
})
export class BeneficiaryListComponent implements OnInit {
  private beneficiaryService = inject(BeneficiaryService);
  private notificationService = inject(NotificationService);

  sidebarOpen = true;
  isLoading = true;
  beneficiaries: Beneficiary[] = [];
  selectedBeneficiary: Beneficiary | null = null;
  showDeleteModal = false;

  ngOnInit() {
    this.loadBeneficiaries();
  }

  loadBeneficiaries() {
    this.beneficiaryService.getBeneficiaries().subscribe({
      next: (response) => {
        this.beneficiaries = response.results;
        this.isLoading = false;
        
        // Show warning if not fully allocated
        const totalAllocation = this.getTotalAllocation();
        if (totalAllocation < 100 && this.beneficiaries.length > 0) {
          this.notificationService.info(
            `You have ${100 - totalAllocation}% unallocated. Consider updating beneficiary allocations.`
          );
        }
      },
      error: (error) => {
        console.error('Error loading beneficiaries:', error);
        this.notificationService.error('Failed to load beneficiaries');
        this.isLoading = false;
      }
    });
  }

  toggleSidebar() {
    this.sidebarOpen = !this.sidebarOpen;
  }

  confirmDelete(beneficiary: Beneficiary) {
    this.selectedBeneficiary = beneficiary;
    this.showDeleteModal = true;
    this.notificationService.warning(`You're about to remove ${beneficiary.name}`);
  }

  deleteBeneficiary() {
    if (this.selectedBeneficiary) {
      const loadingToast = this.notificationService.loading('Removing beneficiary...');
      
      this.beneficiaryService.deleteBeneficiary(this.selectedBeneficiary.uuid).subscribe({
        next: () => {
          loadingToast.dismiss();
          this.notificationService.success(`✓ ${this.selectedBeneficiary!.name} has been removed successfully`);
          this.beneficiaries = this.beneficiaries.filter(b => b.uuid !== this.selectedBeneficiary!.uuid);
          this.showDeleteModal = false;
          this.selectedBeneficiary = null;
        },
        error: (error) => {
          loadingToast.dismiss();
          this.notificationService.error('Failed to remove beneficiary. Please try again.');
          console.error('Delete error:', error);
        }
      });
    }
  }

  getTotalAllocation(): number {
    return this.beneficiaries
      .filter(b => b.status === 'active')
      .reduce((sum, b) => sum + (b.percentage_allocation || 0), 0);
  }

  getStatusClass(status: string): string {
    const classes: { [key: string]: string } = {
      'verified': 'bg-green-100 text-green-800',
      'pending': 'bg-yellow-100 text-yellow-800',
      'rejected': 'bg-red-100 text-red-800'
    };
    return classes[status] || 'bg-gray-100 text-gray-800';
  }

  getInitials(name: string): string {
    return name.split(' ').map(n => n[0]).join('').toUpperCase();
  }
}