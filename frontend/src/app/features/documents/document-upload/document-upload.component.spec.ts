import { ComponentFixture, TestBed } from '@angular/core/testing';
import { ReactiveFormsModule } from '@angular/forms';
import { of } from 'rxjs';
import { DocumentUploadComponent } from './document-upload.component';
import { DocumentService } from '../../../core/services/document.service';
import { NotificationService } from '../../../core/services/notification.service';

describe('DocumentUploadComponent', () => {
  let fixture: ComponentFixture<DocumentUploadComponent>;
  let component: DocumentUploadComponent;
  let notifSpy: jasmine.SpyObj<NotificationService>;

  beforeEach(async () => {
    const documentSpy = jasmine.createSpyObj('DocumentService', ['uploadDocument', 'getDocuments']);
    documentSpy.uploadDocument.and.returnValue(of({} as any));

    notifSpy = jasmine.createSpyObj('NotificationService', [
      'success', 'error', 'warning', 'info', 'loading',
      'refresh', 'initialize', 'getRecentNotifications',
      'markAsRead', 'markAllAsRead', 'clearAll',
    ], { notifications$: of([]), unreadCount$: of(0) });
    notifSpy.loading.and.returnValue('toast-ref' as any);
    notifSpy.refresh.and.returnValue(undefined as any);
    notifSpy.initialize.and.returnValue(undefined as any);
    notifSpy.getRecentNotifications.and.returnValue(of({ results: [], count: 0 } as any));
    notifSpy.markAsRead.and.returnValue(of({} as any));
    notifSpy.markAllAsRead.and.returnValue(of({} as any));
    notifSpy.clearAll.and.returnValue(of({} as any));

    await TestBed.configureTestingModule({
      imports: [DocumentUploadComponent, ReactiveFormsModule],
      providers: [
        { provide: DocumentService, useValue: documentSpy },
        { provide: NotificationService, useValue: notifSpy },
      ],
    }).compileComponents();

    fixture = TestBed.createComponent(DocumentUploadComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });

  it('uploadForm should have title and category controls', () => {
    expect(component.uploadForm.contains('title')).toBeTrue();
    expect(component.uploadForm.contains('category')).toBeTrue();
  });

  it('isUploading should default to false', () => {
    expect(component.isUploading).toBeFalse();
  });

  it('selectedFile should default to null', () => {
    expect(component.selectedFile).toBeNull();
  });

  it('categories should not be empty', () => {
    expect(component.categories.length).toBeGreaterThan(0);
  });

  it('closeModal should emit closeModal event', () => {
    const spy = jasmine.createSpy('closeModal');
    component.closeModal.subscribe(spy);
    component.closeModal.emit();
    expect(spy).toHaveBeenCalled();
  });

  it('onFileSelected should reject file larger than 5MB', () => {
    const largeFile = new File(['x'.repeat(6 * 1024 * 1024)], 'big.pdf', { type: 'application/pdf' });
    const event = { target: { files: [largeFile], value: '' } };
    component.onFileSelected(event);
    expect(component.selectedFile).toBeNull();
    expect(notifSpy.error).toHaveBeenCalled();
  });

  it('onFileSelected should accept file within 5MB', () => {
    const smallFile = new File(['small content'], 'small.pdf', { type: 'application/pdf' });
    const event = { target: { files: [smallFile], value: '' } };
    component.onFileSelected(event);
    expect(component.selectedFile).toBe(smallFile);
  });
});
