import { Component, inject, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormBuilder, FormGroup, Validators, ReactiveFormsModule } from '@angular/forms';
import { Router, ActivatedRoute, RouterModule } from '@angular/router';
import { HeaderComponent } from '../../../shared/components/header/header.component';
import { SidebarComponent } from '../../../shared/components/sidebar/sidebar.component';
import { BeneficiaryService } from '../../../core/services/beneficiary.service';
import { NotificationService } from '../../../core/services/notification.service';
import { Beneficiary } from '../../../core/models/beneficiary.model';

const MAX_FILE_SIZE = 5 * 1024 * 1024; // 5 MB
const ALLOWED_TYPES = new Set(['application/pdf', 'image/jpeg', 'image/jpg', 'image/png']);

@Component({
  selector: 'app-beneficiary-form',
  standalone: true,
  imports: [CommonModule, ReactiveFormsModule, RouterModule, HeaderComponent, SidebarComponent],
  templateUrl: './beneficiary-form.component.html',
  styleUrls: ['./beneficiary-form.component.scss']
})
export class BeneficiaryFormComponent implements OnInit {
  private readonly fb = inject(FormBuilder);
  private readonly router = inject(Router);
  private readonly route = inject(ActivatedRoute);
  private readonly beneficiaryService = inject(BeneficiaryService);
  private readonly notificationService = inject(NotificationService);

  sidebarOpen = true;
  isSubmitting = false;
  isEditMode = false;
  beneficiaryId: string | null = null;
  totalAllocated = 0;
  remainingAllocation = 100;

  // Selected files
  selectedFiles: Record<string, File | null> = {
    identity_document: null,
    birth_certificate: null,
    death_certificate: null,
    additional_documents: null,
  };

  // File names shown in UI
  fileNames: Record<string, string> = {
    identity_document: '',
    birth_certificate: '',
    death_certificate: '',
    additional_documents: '',
  };

  // Existing file URLs (edit mode)
  existingFiles: Record<string, string | null> = {
    identity_document_url: null,
    birth_certificate_url: null,
    death_certificate_url: null,
    additional_documents_url: null,
  };

  beneficiaryForm: FormGroup = this.fb.group({
    name:                   ['', [Validators.required, Validators.minLength(3)]],
    relation:               ['', Validators.required],
    age:                    ['', [Validators.required, Validators.min(0), Validators.max(150)]],
    gender:                 ['', Validators.required],
    phone_number:           [''],
    profession:             [''],
    salary_range:           [''],
    percentage_allocation:  [0, [Validators.required, Validators.min(0), Validators.max(100)]],
    death_certificate_number: [''],
  });

  ngOnInit() {
    this.loadCurrentAllocation();

    this.route.params.subscribe(params => {
      if (params['id']) {
        this.isEditMode = true;
        this.beneficiaryId = params['id'];
        this.loadBeneficiary();
      }
    });

    this.beneficiaryForm.get('percentage_allocation')?.valueChanges.subscribe(value => {
      this.validateAllocation(value);
    });
  }

  toggleSidebar() { this.sidebarOpen = !this.sidebarOpen; }

  // ── Allocation helpers ──────────────────────────────────────────────────────

  loadCurrentAllocation() {
    this.beneficiaryService.getBeneficiaries().subscribe({
      next: (response) => {
        const beneficiaries = response.results ?? [];
        this.totalAllocated = beneficiaries
          .filter(b => b.status === 'active' && b.uuid !== this.beneficiaryId)
          .reduce((sum, b) => sum + Number(b.percentage_allocation || 0), 0);
        this.remainingAllocation = 100 - this.totalAllocated;
      }
    });
  }

  validateAllocation(value: number) {
    if (value > this.remainingAllocation) {
      this.beneficiaryForm.get('percentage_allocation')?.setErrors({
        maxExceeded: true,
        message: `Only ${this.remainingAllocation}% remaining`
      });
    }
  }

  getAllocationClass(): string {
    const value = this.beneficiaryForm.get('percentage_allocation')?.value || 0;
    if (value > this.remainingAllocation) return 'text-red-600';
    if (value >= this.remainingAllocation * 0.8) return 'text-yellow-600';
    return 'text-green-600';
  }

  // ── Load beneficiary (edit mode) ────────────────────────────────────────────

  loadBeneficiary() {
    if (!this.beneficiaryId) return;
    this.beneficiaryService.getBeneficiary(this.beneficiaryId).subscribe({
      next: (b: Beneficiary) => {
        this.beneficiaryForm.patchValue({
          name: b.name,
          relation: b.relation,
          age: b.age,
          gender: b.gender,
          phone_number: b.phone_number ?? '',
          profession: b.profession ?? '',
          salary_range: b.salary_range ?? '',
          percentage_allocation: b.percentage_allocation,
          death_certificate_number: b.death_certificate_number ?? '',
        });
        this.existingFiles = {
          identity_document_url:     b.identity_document_url     ?? null,
          birth_certificate_url:     b.birth_certificate_url     ?? null,
          death_certificate_url:     b.death_certificate_url     ?? null,
          additional_documents_url:  b.additional_documents_url  ?? null,
        };
      },
      error: (_err: unknown) => this.notificationService.error('Failed to load beneficiary'),
    });
  }

  // ── File handling ───────────────────────────────────────────────────────────

  onFileSelected(event: Event, fieldName: string) {
    const input = event.target as HTMLInputElement;
    const file = input.files?.[0];
    if (!file) return;

    if (file.size > MAX_FILE_SIZE) {
      this.notificationService.error('File too large — maximum size is 5 MB');
      input.value = '';
      return;
    }
    if (!ALLOWED_TYPES.has(file.type)) {
      this.notificationService.error('Invalid file type — only PDF, JPG, and PNG are accepted');
      input.value = '';
      return;
    }

    this.selectedFiles[fieldName] = file;
    this.fileNames[fieldName] = file.name;
  }

  openExistingFile(url: string | null) {
    if (url) window.open(url, '_blank');
  }

  // ── Submit ──────────────────────────────────────────────────────────────────

  onSubmit() {
    if (this.beneficiaryForm.invalid) {
      Object.keys(this.beneficiaryForm.controls).forEach(k =>
        this.beneficiaryForm.get(k)?.markAsTouched()
      );
      this.notificationService.error('Please fill all required fields correctly');
      return;
    }

    // Identity document is required when creating
    if (!this.isEditMode && !this.selectedFiles['identity_document']) {
      this.notificationService.error('Identity document is required');
      return;
    }

    this.isSubmitting = true;
    const formData = new FormData();

    Object.entries(this.beneficiaryForm.value).forEach(([key, value]) => {
      if (value !== null && value !== undefined && value !== '') {
        if (typeof value === 'string' || typeof value === 'number' || typeof value === 'boolean') {
          formData.append(key, String(value));
        }
      }
    });

    Object.entries(this.selectedFiles).forEach(([key, file]) => {
      if (file) formData.append(key, file);
    });

    const request$ = this.isEditMode && this.beneficiaryId
      ? this.beneficiaryService.updateBeneficiary(this.beneficiaryId, formData)
      : this.beneficiaryService.createBeneficiary(formData);

    request$.subscribe({
      next: () => this.router.navigate(['/beneficiary']),
      error: (err) => {
        const detail = err?.error?.percentage_allocation?.[0]
          ?? err?.error?.non_field_errors?.[0]
          ?? `Failed to ${this.isEditMode ? 'update' : 'add'} beneficiary`;
        this.notificationService.error(detail);
        this.isSubmitting = false;
      },
    });
  }
}
