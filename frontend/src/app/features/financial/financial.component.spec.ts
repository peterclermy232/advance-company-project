import { ComponentFixture, TestBed } from '@angular/core/testing';
import { provideRouter } from '@angular/router';
import { of } from 'rxjs';
import { FinancialComponent } from './financial.component';
import { AuthService } from '../../core/services/auth.service';
import { NotificationService } from '../../core/services/notification.service';
import { FinancialService } from '../../core/services/financial.service';
import { ToastService } from '../../core/services/toast.service';
import { Deposit } from '../../core/models/financial.model';

describe('FinancialComponent', () => {
  let fixture: ComponentFixture<FinancialComponent>;
  let component: FinancialComponent;
  let authSpy: jasmine.SpyObj<AuthService>;
  let financialSpy: jasmine.SpyObj<FinancialService>;

  const makeDeposit = (status: string): Deposit =>
    ({ uuid: status, amount: '20000', status, payment_method: 'mpesa' } as any);

  beforeEach(async () => {
    authSpy = jasmine.createSpyObj('AuthService', ['isAdmin', 'logout', 'getCurrentUser'], {
      currentUser$: of(null),
    });
    authSpy.isAdmin.and.returnValue(false);

    financialSpy = jasmine.createSpyObj('FinancialService', [
      'getDeposits', 'approveDeposit', 'rejectDeposit',
    ]);
    financialSpy.getDeposits.and.returnValue(of({ results: [] } as any));

    const toastSpy = jasmine.createSpyObj('ToastService', ['success', 'error', 'warning', 'info']);

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
      imports: [FinancialComponent],
      providers: [
        provideRouter([]),
        { provide: AuthService, useValue: authSpy },
        { provide: FinancialService, useValue: financialSpy },
        { provide: ToastService, useValue: toastSpy },
        { provide: NotificationService, useValue: notifSpy },
      ],
    }).compileComponents();

    fixture = TestBed.createComponent(FinancialComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });

  it('isAdmin should delegate to AuthService', () => {
    authSpy.isAdmin.and.returnValue(true);
    expect(component.isAdmin).toBeTrue();
  });

  it('pendingDeposits should filter by pending and processing status', () => {
    component.allDeposits = [
      makeDeposit('pending'),
      makeDeposit('processing'),
      makeDeposit('completed'),
      makeDeposit('failed'),
    ];
    expect(component.pendingDeposits.length).toBe(2);
  });

  it('approvedDeposits should filter by completed status', () => {
    component.allDeposits = [makeDeposit('completed'), makeDeposit('pending')];
    expect(component.approvedDeposits.length).toBe(1);
  });

  it('rejectedDeposits should filter by failed status', () => {
    component.allDeposits = [makeDeposit('failed'), makeDeposit('completed')];
    expect(component.rejectedDeposits.length).toBe(1);
  });

  it('filteredDeposits with filterStatus="pending" should include processing', () => {
    component.allDeposits = [makeDeposit('pending'), makeDeposit('processing'), makeDeposit('completed')];
    component.filterStatus = 'pending';
    expect(component.filteredDeposits.length).toBe(2);
  });

  it('sidebarOpen should default to true', () => {
    expect(component.sidebarOpen).toBeTrue();
  });
});
