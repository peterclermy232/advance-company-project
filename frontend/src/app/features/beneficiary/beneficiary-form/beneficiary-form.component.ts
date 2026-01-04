import { Component, inject, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormBuilder, FormGroup, Validators, ReactiveFormsModule } from '@angular/forms';
import { Router, ActivatedRoute, RouterModule } from '@angular/router';
import { HeaderComponent } from '../../../shared/components/header/header.component';
import { SidebarComponent } from '../../../shared/components/sidebar/sidebar.component';
import { BeneficiaryService } from '../../../core/services/beneficiary.service';
import { NotificationService } from '../../../core/services/notification.service';

@Component({
  selector: 'app-beneficiary-form',
  standalone: true,
  imports: [CommonModule, ReactiveFormsModule, RouterModule, HeaderComponent, SidebarComponent],
  templateUrl: './beneficiary-form.component.html',
  styleUrls: ['./beneficiary-form.component.scss']
})
export class BeneficiaryFormComponent implements OnInit {
  private fb = inject(FormBuilder);
  private router = inject(Router);
  private route = inject(ActivatedRoute);
  private beneficiaryService = inject(BeneficiaryService);
  private notificationService = inject(NotificationService);

  sidebarOpen = true;
  isSubmitting = false;
  isEditMode = false;
  beneficiaryId: number | null = null;
  beneficiaryForm: FormGroup;

  selectedFiles: { [key: string]: File | null } = {
    identity_document: null,
    birth_certificate: null,
    death_certificate: null
  };

  constructor() {
    this.beneficiaryForm = this.fb.group({
      name: ['', [Validators.required, Validators.minLength(3)]],
      relation: ['', Validators.required],
      age: ['', [Validators.required, Validators.min(0)]],
      gender: ['', Validators.required],
      phone_number: [''],
      profession: [''],
      salary_range: [''],
      death_certificate_number: ['']
    });
  }

  ngOnInit() {
    this.route.params.subscribe(params => {
      if (params['id']) {
        this.isEditMode = true;
        this.beneficiaryId = +params['id'];
        this.loadBeneficiary();
      }
    });
  }

  loadBeneficiary() {
    if (this.beneficiaryId) {
      this.beneficiaryService.getBeneficiary(this.beneficiaryId).subscribe({
        next: (beneficiary) => {
          this.beneficiaryForm.patchValue(beneficiary);
        },
        error: (error) => {
          this.notificationService.error('Failed to load beneficiary');
        }
      });
    }
  }

  toggleSidebar() {
    this.sidebarOpen = !this.sidebarOpen;
  }

  onFileSelected(event: any, fieldName: string) {
    const file = event.target.files[0];
    if (file) {
      this.selectedFiles[fieldName] = file;
    }
  }

  onSubmit() {
    if (this.beneficiaryForm.valid) {
      this.isSubmitting = true;
      const formData = new FormData();
      
      Object.keys(this.beneficiaryForm.value).forEach(key => {
        const value = this.beneficiaryForm.value[key];
        if (value !== null && value !== '') {
          formData.append(key, value);
        }
      });

      Object.keys(this.selectedFiles).forEach(key => {
        const file = this.selectedFiles[key];
        if (file) {
          formData.append(key, file);
        }
      });

      const request = this.isEditMode && this.beneficiaryId
        ? this.beneficiaryService.updateBeneficiary(this.beneficiaryId, formData)
        : this.beneficiaryService.createBeneficiary(formData);

      request.subscribe({
        next: () => {
          this.notificationService.success(`Beneficiary ${this.isEditMode ? 'updated' : 'added'} successfully`);
          this.router.navigate(['/beneficiary']);
        },
        error: (error) => {
          this.notificationService.error(`Failed to ${this.isEditMode ? 'update' : 'add'} beneficiary`);
          this.isSubmitting = false;
        }
      });
    } else {
      Object.keys(this.beneficiaryForm.controls).forEach(key => {
        this.beneficiaryForm.get(key)?.markAsTouched();
      });
    }
  }
}