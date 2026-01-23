import { Component, inject, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormBuilder, FormGroup, Validators, ReactiveFormsModule } from '@angular/forms';
import { HeaderComponent } from '../../../shared/components/header/header.component';
import { SidebarComponent } from '../../../shared/components/sidebar/sidebar.component';
import { LoadingComponent } from '../../../shared/components/loading/loading.component';
import { DocumentService } from '../../../core/services/document.service';
import { NotificationService } from '../../../core/services/notification.service';
import { AuthService } from '../../../core/services/auth.service';
import { Document } from '../../../core/models/document.model';

@Component({
  selector: 'app-document-list',
  standalone: true,
  imports: [CommonModule, ReactiveFormsModule, HeaderComponent, SidebarComponent, LoadingComponent],
  templateUrl: './document-list.component.html',
  styleUrls: ['./document-list.component.scss']
})
export class DocumentListComponent implements OnInit {
  private fb = inject(FormBuilder);
  private documentService = inject(DocumentService);
  private notificationService = inject(NotificationService);
  private authService = inject(AuthService);

  sidebarOpen = true;
  isLoading = true;
  isUploading = false;
  showUploadModal = false;
  uploadProgress = 0;
  
  documents: Document[] = [];
  documentsByCategory: { [key: string]: Document[] } = {};
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

  ngOnInit() {
    this.loadDocuments();
  }

  loadDocuments() {
    this.documentService.getDocuments().subscribe({
      next: (documents) => {
        this.documents = documents;
        this.groupDocumentsByCategory();
        this.isLoading = false;
      },
      error: () => {
        this.isLoading = false;
      }
    });
  }

  groupDocumentsByCategory() {
    this.documentsByCategory = {};
    this.categories.forEach(cat => {
      this.documentsByCategory[cat.value] =
        this.documents?.filter(doc => doc.category === cat.value) ?? [];
    });
  }

  toggleSidebar() {
    this.sidebarOpen = !this.sidebarOpen;
  }

  openUploadModal() {
    this.showUploadModal = true;
    this.uploadForm.reset();
    this.selectedFile = null;
    this.uploadProgress = 0;
  }

  closeUploadModal() {
    this.showUploadModal = false;
    this.uploadProgress = 0;
  }

  onFileSelected(event: any) {
    const file = event.target.files[0];
    if (file) {
      // Check file size (5MB max)
      const maxSize = 5 * 1024 * 1024; // 5MB
      if (file.size > maxSize) {
        this.notificationService.error(
          `File too large: ${(file.size / 1024 / 1024).toFixed(2)}MB. Maximum: 5MB`
        );
        event.target.value = ''; // Clear input
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

      // Show upload toast
      const uploadToast = this.notificationService.loading(
        `Uploading "${this.selectedFile.name}"...`
      );

      // Simulate progress for user feedback
      const progressInterval = setInterval(() => {
        if (this.uploadProgress < 90) {
          this.uploadProgress += 10;
        }
      }, 500);

      this.documentService.uploadDocument(formData).subscribe({
        next: (document) => {
          clearInterval(progressInterval);
          this.uploadProgress = 100;
          
          uploadToast.dismiss();
          this.notificationService.success(
            `✓ "${document.title}" uploaded successfully!`
          );
          
          this.documents.unshift(document);
          this.groupDocumentsByCategory();
          this.closeUploadModal();
          this.isUploading = false;
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

  deleteDocument(doc: Document) {
    if (confirm(`Delete "${doc.title}"? This cannot be undone.`)) {
      const loadingToast = this.notificationService.loading('Deleting...');
      
      this.documentService.deleteDocument(doc.id).subscribe({
        next: () => {
          loadingToast.dismiss();
          this.notificationService.success(`✓ "${doc.title}" deleted`);
          this.documents = this.documents.filter(d => d.id !== doc.id);
          this.groupDocumentsByCategory();
        },
        error: () => {
          loadingToast.dismiss();
          this.notificationService.error('Delete failed');
        }
      });
    }
  }

  verifyDocument(doc: Document) {
    const loadingToast = this.notificationService.loading('Verifying...');
    
    this.documentService.verifyDocument(doc.id).subscribe({
      next: () => {
        loadingToast.dismiss();
        this.notificationService.success(`✓ "${doc.title}" verified`);
        doc.status = 'verified';
      },
      error: () => {
        loadingToast.dismiss();
        this.notificationService.error('Verification failed');
      }
    });
  }

  getStatusClass(status: string): string {
    const classes: { [key: string]: string } = {
      'verified': 'bg-green-100 text-green-800',
      'pending': 'bg-yellow-100 text-yellow-800',
      'rejected': 'bg-red-100 text-red-800'
    };
    return classes[status] || 'bg-gray-100 text-gray-800';
  }

  getCategoryLabel(category: string): string {
    const cat = this.categories.find(c => c.value === category);
    return cat ? cat.label : category;
  }

  isAdmin(): boolean {
    return this.authService.isAdmin();
  }

  openDocument(url: string) {
    window.open(url, '_blank');
  }
}