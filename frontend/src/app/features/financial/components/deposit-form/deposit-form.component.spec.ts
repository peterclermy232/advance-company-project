import { ComponentFixture, TestBed } from '@angular/core/testing';
import { ReactiveFormsModule } from '@angular/forms';
import { provideRouter } from '@angular/router';
import { of } from 'rxjs';
import { DepositFormComponent } from './deposit-form.component';
import { FinancialService } from '../../../../core/services/financial.service';
import { ToastService } from '../../../../core/services/toast.service';
import { AuthService } from '../../../../core/services/auth.service';
import { NotificationService } from '../../../../core/services/notification.service';

describe('DepositFormComponent', () => {
  let fixture: ComponentFixture<DepositFormComponent>;
  let component: DepositFormComponent;
  let financialSpy: jasmine.SpyObj<FinancialService>;

  beforeEach(async () => {
    financialSpy = jasmine.createSpyObj('FinancialService', ['canDeposit', 'createDeposit', 'initiateDeposit']);
    financialSpy.canDeposit.and.returnValue(of({ can_deposit: true, message: '' } as any));

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
      imports: [DepositFormComponent, ReactiveFormsModule],
      providers: [
        provideRouter([]),
        { provide: FinancialService, useValue: financialSpy },
        { provide: ToastService, useValue: toastSpy },
        { provide: AuthService, useValue: authSpy },
        { provide: NotificationService, useValue: notifSpy },
      ],
    }).compileComponents();

    fixture = TestBed.createComponent(DepositFormComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });

  it('depositForm should have amount and payment_method controls', () => {
    expect(component.depositForm.contains('amount')).toBeTrue();
    expect(component.depositForm.contains('payment_method')).toBeTrue();
  });

  it('MONTHLY_DEPOSIT_AMOUNT should be 20000', () => {
    expect(component.MONTHLY_DEPOSIT_AMOUNT).toBe(20000);
  });

  it('amount should be disabled (fixed)', () => {
    expect(component.depositForm.get('amount')!.disabled).toBeTrue();
  });

  it('payment_method should default to "mpesa"', () => {
    expect(component.depositForm.get('payment_method')!.value).toBe('mpesa');
  });

  it('mpesa_phone should be required when payment_method is mpesa', () => {
    component.depositForm.get('mpesa_phone')!.setValue('');
    expect(component.depositForm.get('mpesa_phone')!.valid).toBeFalse();
  });

  it('isSubmitting should default to false', () => {
    expect(component.isSubmitting).toBeFalse();
  });

  it('depositCreated EventEmitter should exist', () => {
    expect(component.depositCreated).toBeTruthy();
  });

  it('formCancelled EventEmitter should exist', () => {
    expect(component.formCancelled).toBeTruthy();
  });
});
