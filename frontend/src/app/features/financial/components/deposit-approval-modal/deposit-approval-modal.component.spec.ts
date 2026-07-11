import { ComponentFixture, TestBed } from '@angular/core/testing';
import { DepositApprovalModalComponent } from './deposit-approval-modal.component';

describe('DepositApprovalModalComponent', () => {
  let fixture: ComponentFixture<DepositApprovalModalComponent>;
  let component: DepositApprovalModalComponent;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [DepositApprovalModalComponent],
    }).compileComponents();

    fixture = TestBed.createComponent(DepositApprovalModalComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });

  it('should default isOpen to false', () => {
    expect(component.isOpen).toBeFalse();
  });

  it('should default deposit to null', () => {
    expect(component.deposit).toBeNull();
  });

  it('should default isProcessing to false', () => {
    expect(component.isProcessing).toBeFalse();
  });

  it('onConfirm should emit confirm event', () => {
    const spy = jasmine.createSpy('confirm');
    component.confirm.subscribe(spy);
    component.onConfirm();
    expect(spy).toHaveBeenCalled();
  });

  it('onCancel should emit cancel event', () => {
    const spy = jasmine.createSpy('cancel');
    component.cancel.subscribe(spy);
    component.onCancel();
    expect(spy).toHaveBeenCalled();
  });

  it('getPaymentMethodLabel should return "M-Pesa" for "mpesa"', () => {
    expect(component.getPaymentMethodLabel('mpesa')).toBe('M-Pesa');
  });

  it('getPaymentMethodLabel should return "Bank Transfer" for "bank"', () => {
    expect(component.getPaymentMethodLabel('bank')).toBe('Bank Transfer');
  });

  it('getPaymentMethodLabel should return the raw value for unknown method', () => {
    expect(component.getPaymentMethodLabel('cash')).toBe('cash');
  });
});
