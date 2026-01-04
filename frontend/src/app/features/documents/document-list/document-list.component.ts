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
      next: (response) => {
        this.documents = response.results;
        this.groupDocumentsByCategory();
        this.isLoading = false;
      },
      error: (error) => {
        console.error('Error loading documents:', error);
        this.isLoading = false;
      }
    });
  }

  groupDocumentsByCategory() {
    this.documentsByCategory = {};
    this.categories.forEach(cat => {
      this.documentsByCategory[cat.value] = this.documents.filter(
        doc => doc.category === cat.value
      );
    });
  }

  toggleSidebar() {
    this.sidebarOpen = !this.sidebarOpen;
  }

  openUploadModal() {
    this.showUploadModal = true;
    this.uploadForm.reset();
    this.selectedFile = null;
  }

  closeUploadModal() {
    this.showUploadModal = false;
  }

  onFileSelected(event: any) {
    const file = event.target.files[0];
    if (file) {
      this.selectedFile = file;
    }
  }

  onUpload() {
    if (this.uploadForm.valid && this.selectedFile) {
      this.isUploading = true;
      const formData = new FormData();
      formData.append('title', this.uploadForm.value.title);
      formData.append('category', this.uploadForm.value.category);
      formData.append('file', this.selectedFile);

      this.documentService.uploadDocument(formData).subscribe({
        next: (document) => {
          this.notificationService.success('Document uploaded successfully');
          this.documents.unshift(document);
          this.groupDocumentsByCategory();
          this.closeUploadModal();
          this.isUploading = false;
        },
        error: (error) => {
          this.notificationService.error('Failed to upload document');
          this.isUploading = false;
        }
      });
    }
  }

  deleteDocument(doc: Document) {
    if (confirm(`Are you sure you want to delete ${doc.title}?`)) {
      this.documentService.deleteDocument(doc.id).subscribe({
        next: () => {
          this.notificationService.success('Document deleted successfully');
          this.documents = this.documents.filter(d => d.id !== doc.id);
          this.groupDocumentsByCategory();
        },
        error: (error) => {
          this.notificationService.error('Failed to delete document');
        }
      });
    }
  }

  verifyDocument(doc: Document) {
    this.documentService.verifyDocument(doc.id).subscribe({
      next: () => {
        this.notificationService.success('Document verified');
        doc.status = 'verified';
      },
      error: (error) => {
        this.notificationService.error('Failed to verify document');
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
}
