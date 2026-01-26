import { Component, EventEmitter, inject, Input, Output } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormBuilder, FormGroup, Validators, ReactiveFormsModule } from '@angular/forms';
import { DocumentService } from '../../../core/services/document.service';
import { NotificationService } from '../../../core/services/notification.service';

@Component({
  selector: 'app-document-upload',
  standalone: true,
  imports: [CommonModule, ReactiveFormsModule],
  templateUrl: './document-upload.component.html',
  styleUrls: ['./document-upload.component.scss']
})
export class DocumentUploadComponent {
  private fb = inject(FormBuilder);
  private documentService = inject(DocumentService);
  private notificationService = inject(NotificationService);

  @Input() showModal = false;
  @Output() closeModal = new EventEmitter<void>();
  @Output() uploadSuccess = new EventEmitter<void>();

  isUploading = false;
  uploadProgress = 0;
  uploadForm: FormGroup;
  selectedFile: File | null = null;

  categories = [
    { value: 'identity', label: 'Identity Documents' },
    { value: 'beneficiary', label: 'Beneficiary Documents' },
    { value: 'birth_certificate', label: 'Birth Certificates' },
    { value: 'death_certificate', label: 'Death Certificates' },
    { value: 'additional', label: 'Additional Documents' }
  ];

  constructor() {
    this.uploadForm = this.fb.group({
      title: ['', Validators.required],
      category: ['', Validators.required]
    });
  }

  onFileSelected(event: any) {
    const file = event.target.files[0];
    if (file) {
      const maxSize = 5 * 1024 * 1024; // 5MB
      if (file.size > maxSize) {
        this.notificationService.error(
          `File too large: ${(file.size / 1024 / 1024).toFixed(2)}MB. Maximum: 5MB`
        );
        event.target.value = '';
        return;
      }
      
      this.selectedFile = file;
      console.log('✓ File selected:', file.name, `${(file.size / 1024).toFixed(0)}KB`);
    }
  }

  onUpload() {
    if (this.uploadForm.valid && this.selectedFile) {
      this.isUploading = true;
      this.uploadProgress = 0;

      const formData = new FormData();
      formData.append('title', this.uploadForm.value.title);
      formData.append('category', this.uploadForm.value.category);
      formData.append('file', this.selectedFile);

      const uploadToast = this.notificationService.loading(
        `Uploading "${this.selectedFile.name}"...`
      );

      const progressInterval = setInterval(() => {
        if (this.uploadProgress < 90) {
          this.uploadProgress += 10;
        }
      }, 500);

      this.documentService.uploadDocument(formData).subscribe({
        next: (response: any) => {
          clearInterval(progressInterval);
          this.uploadProgress = 100;
          
          uploadToast.dismiss();
          this.notificationService.success(
            `✓ "${response.document?.title || 'Document'}" uploaded successfully!`
          );
          
          this.isUploading = false;
          this.resetForm();
          this.uploadSuccess.emit();
          this.close();
        },
        error: (error) => {
          clearInterval(progressInterval);
          uploadToast.dismiss();
          
          const errorMsg = error?.error?.error || 'Upload failed. Please try again.';
          this.notificationService.error(errorMsg);
          
          this.isUploading = false;
          this.uploadProgress = 0;
        }
      });
    }
  }

  close() {
    if (!this.isUploading) {
      this.resetForm();
      this.closeModal.emit();
    }
  }

  resetForm() {
    this.uploadForm.reset();
    this.selectedFile = null;
    this.uploadProgress = 0;
  }
}