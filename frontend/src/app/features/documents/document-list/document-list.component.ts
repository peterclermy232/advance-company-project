import { Component, inject, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { HeaderComponent } from '../../../shared/components/header/header.component';
import { SidebarComponent } from '../../../shared/components/sidebar/sidebar.component';
import { LoadingComponent } from '../../../shared/components/loading/loading.component';
import { DocumentUploadComponent } from '../document-upload/document-upload.component';
import { DocumentService } from '../../../core/services/document.service';
import { NotificationService } from '../../../core/services/notification.service';
import { AuthService } from '../../../core/services/auth.service';
import { Document } from '../../../core/models/document.model';

@Component({
  selector: 'app-document-list',
  standalone: true,
  imports: [
    CommonModule, 
    HeaderComponent, 
    SidebarComponent, 
    LoadingComponent,
    DocumentUploadComponent
  ],
  templateUrl: './document-list.component.html',
  styleUrls: ['./document-list.component.scss']
})
export class DocumentListComponent implements OnInit {
  private documentService = inject(DocumentService);
  private notificationService = inject(NotificationService);
  private authService = inject(AuthService);

  sidebarOpen = true;
  isLoading = true;
  showUploadModal = false;
  
  documents: Document[] = [];
  documentsByCategory: { [key: string]: Document[] } = {};

  categories = [
    { value: 'identity', label: 'Identity Documents' },
    { value: 'beneficiary', label: 'Beneficiary Documents' },
    { value: 'birth_certificate', label: 'Birth Certificates' },
    { value: 'death_certificate', label: 'Death Certificates' },
    { value: 'additional', label: 'Additional Documents' }
  ];

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
  }

  closeUploadModal() {
    this.showUploadModal = false;
  }

  onUploadSuccess() {
    // Reload all documents from server after successful upload
    this.loadDocuments();
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
        
        const index = this.documents.findIndex(d => d.id === doc.id);
        if (index !== -1) {
          this.documents = [
            ...this.documents.slice(0, index),
            { ...this.documents[index], status: 'verified' },
            ...this.documents.slice(index + 1)
          ];
          this.groupDocumentsByCategory();
        }
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