import { ComponentFixture, TestBed } from '@angular/core/testing';
import { provideRouter } from '@angular/router';
import { of } from 'rxjs';
import { DocumentListComponent } from './document-list.component';
import { DocumentService } from '../../../core/services/document.service';
import { AuthService } from '../../../core/services/auth.service';
import { NotificationService } from '../../../core/services/notification.service';

describe('DocumentListComponent', () => {
  let fixture: ComponentFixture<DocumentListComponent>;
  let component: DocumentListComponent;

  beforeEach(async () => {
    const documentSpy = jasmine.createSpyObj('DocumentService', [
      'getDocuments', 'uploadDocument', 'deleteDocument',
    ]);
    documentSpy.getDocuments.and.returnValue(of([] as any));

    const authSpy = jasmine.createSpyObj('AuthService', ['isAdmin', 'logout', 'getCurrentUser'], {
      currentUser$: of(null),
    });
    authSpy.isAdmin.and.returnValue(false);

    const notifSpy = jasmine.createSpyObj('NotificationService', [
      'success', 'error', 'warning', 'info', 'loading',
      'refresh', 'initialize', 'getRecentNotifications',
      'markAsRead', 'markAllAsRead', 'clearAll',
    ], { notifications$: of([]), unreadCount$: of(0) });
    notifSpy.refresh.and.returnValue(undefined as any);
    notifSpy.initialize.and.returnValue(undefined as any);
    notifSpy.getRecentNotifications.and.returnValue(of({ results: [], count: 0 } as any));
    notifSpy.markAsRead.and.returnValue(of({} as any));
    notifSpy.markAllAsRead.and.returnValue(of({} as any));
    notifSpy.clearAll.and.returnValue(of({} as any));

    await TestBed.configureTestingModule({
      imports: [DocumentListComponent],
      providers: [
        provideRouter([]),
        { provide: DocumentService, useValue: documentSpy },
        { provide: AuthService, useValue: authSpy },
        { provide: NotificationService, useValue: notifSpy },
      ],
    }).compileComponents();

    fixture = TestBed.createComponent(DocumentListComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });

  it('should default sidebarOpen to true', () => {
    expect(component.sidebarOpen).toBeTrue();
  });

  it('should default showUploadModal to false', () => {
    expect(component.showUploadModal).toBeFalse();
  });

  it('categories should not be empty', () => {
    expect(component.categories.length).toBeGreaterThan(0);
  });

  it('each category should have a value and label', () => {
    component.categories.forEach(cat => {
      expect(cat.value).toBeTruthy();
      expect(cat.label).toBeTruthy();
    });
  });
});
