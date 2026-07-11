import { ComponentFixture, TestBed } from '@angular/core/testing';
import { ReactiveFormsModule } from '@angular/forms';
import { provideRouter } from '@angular/router';
import { of } from 'rxjs';
import { DepositHistoryComponent } from './deposit-history.component';
import { FinancialService } from '../../../../core/services/financial.service';
import { ToastService } from '../../../../core/services/toast.service';
import { AuthService } from '../../../../core/services/auth.service';
import { NotificationService } from '../../../../core/services/notification.service';
import { Deposit } from '../../../../core/models/financial.model';

describe('DepositHistoryComponent', () => {
  let fixture: ComponentFixture<DepositHistoryComponent>;
  let component: DepositHistoryComponent;

  const makeDeposit = (status: string): Deposit =>
    ({ uuid: status, amount: '20000', status, payment_method: 'mpesa' } as any);

  beforeEach(async () => {
    const financialSpy = jasmine.createSpyObj('FinancialService', [
      'getDeposits', 'approveDeposit', 'rejectDeposit',
    ]);
    financialSpy.getDeposits.and.returnValue(of({ results: [] } as any));

    const toastSpy = jasmine.createSpyObj('ToastService', ['success', 'error', 'warning', 'info']);

    const authSpy = jasmine.createSpyObj('AuthService', ['isAdmin', 'logout', 'getCurrentUser'], {
      currentUser$: of(null),
    });
    authSpy.isAdmin.and.returnValue(false);

    const notifSpy = jasmine.createSpyObj('NotificationService', [
      'refresh', 'initialize', 'getRecentNotifications',
      'markAsRead', 'markAllAsRead', 'clearAll',
      'success', 'error', 'warning', 'info', 'loading',
    ], { notifications$: of([]), unreadCount$: of(0) });
    notifSpy.refresh.and.returnValue(undefined as any);
    notifSpy.initialize.and.returnValue(undefined as any);
    notifSpy.getRecentNotifications.and.returnValue(of({ results: [], count: 0 } as any));
    notifSpy.markAsRead.and.returnValue(of({} as any));
    notifSpy.markAllAsRead.and.returnValue(of({} as any));
    notifSpy.clearAll.and.returnValue(of({} as any));

    await TestBed.configureTestingModule({
      imports: [DepositHistoryComponent, ReactiveFormsModule],
      providers: [
        provideRouter([]),
        { provide: FinancialService, useValue: financialSpy },
        { provide: ToastService, useValue: toastSpy },
        { provide: AuthService, useValue: authSpy },
        { provide: NotificationService, useValue: notifSpy },
      ],
    }).compileComponents();

    fixture = TestBed.createComponent(DepositHistoryComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });

  it('should default sidebarOpen to true', () => {
    expect(component.sidebarOpen).toBeTrue();
  });

  it('should default filterStatus to "pending"', () => {
    expect(component.filterStatus).toBe('pending');
  });

  it('pendingDeposits should filter by pending status', () => {
    component.allDeposits = [makeDeposit('pending'), makeDeposit('completed')];
    expect(component.pendingDeposits.length).toBe(1);
  });

  it('approvedDeposits should filter by completed status', () => {
    component.allDeposits = [makeDeposit('completed'), makeDeposit('failed')];
    expect(component.approvedDeposits.length).toBe(1);
  });

  it('rejectForm should have a reason control', () => {
    expect(component.rejectForm.contains('reason')).toBeTrue();
  });
});
