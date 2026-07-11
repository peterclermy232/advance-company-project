import { ComponentFixture, TestBed } from '@angular/core/testing';
import { provideRouter } from '@angular/router';
import { FormsModule } from '@angular/forms';
import { of } from 'rxjs';
import { BeneficiaryVerificationComponent } from './beneficiary-verification.component';
import { ApiService } from '../../../core/services/api.service';
import { ToastService } from '../../../core/services/toast.service';
import { AuthService } from '../../../core/services/auth.service';
import { NotificationService } from '../../../core/services/notification.service';

describe('BeneficiaryVerificationComponent', () => {
  let fixture: ComponentFixture<BeneficiaryVerificationComponent>;
  let component: BeneficiaryVerificationComponent;

  beforeEach(async () => {
    const apiSpy = jasmine.createSpyObj('ApiService', ['get', 'post', 'patch']);
    apiSpy.get.and.returnValue(of({ results: [], pending: 0, verified: 0, rejected: 0 } as any));
    apiSpy.post.and.returnValue(of({} as any));
    apiSpy.patch.and.returnValue(of({} as any));

    const toastSpy = jasmine.createSpyObj('ToastService', ['success', 'error', 'warning', 'info']);

    const authSpy = jasmine.createSpyObj('AuthService', ['isAdmin', 'logout', 'getCurrentUser'], {
      currentUser$: of(null),
    });
    authSpy.isAdmin.and.returnValue(true);

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
      imports: [BeneficiaryVerificationComponent, FormsModule],
      providers: [
        provideRouter([]),
        { provide: ApiService, useValue: apiSpy },
        { provide: ToastService, useValue: toastSpy },
        { provide: AuthService, useValue: authSpy },
        { provide: NotificationService, useValue: notifSpy },
      ],
    }).compileComponents();

    fixture = TestBed.createComponent(BeneficiaryVerificationComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });

  it('should default sidebarOpen to true', () => {
    expect(component.sidebarOpen).toBeTrue();
  });
});
