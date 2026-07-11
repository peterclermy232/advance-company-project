import { ComponentFixture, TestBed } from '@angular/core/testing';
import { DepositRejectionModalComponent } from './deposit-rejection-modal.component';
import { SimpleChange } from '@angular/core';

describe('DepositRejectionModalComponent', () => {
  let fixture: ComponentFixture<DepositRejectionModalComponent>;
  let component: DepositRejectionModalComponent;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [DepositRejectionModalComponent],
    }).compileComponents();

    fixture = TestBed.createComponent(DepositRejectionModalComponent);
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

  it('should have a reason control in rejectForm', () => {
    expect(component.rejectForm.contains('reason')).toBeTrue();
  });

  it('reason should be required', () => {
    component.rejectForm.get('reason')!.setValue('');
    expect(component.rejectForm.get('reason')!.valid).toBeFalse();
  });

  it('onSubmit should emit reason when form is valid', () => {
    const spy = jasmine.createSpy('confirm');
    component.confirm.subscribe(spy);
    component.rejectForm.get('reason')!.setValue('Duplicate entry');
    component.onSubmit();
    expect(spy).toHaveBeenCalledWith('Duplicate entry');
  });

  it('onSubmit should not emit when form is invalid', () => {
    const spy = jasmine.createSpy('confirm');
    component.confirm.subscribe(spy);
    component.rejectForm.get('reason')!.setValue('');
    component.onSubmit();
    expect(spy).not.toHaveBeenCalled();
  });

  it('onCancel should emit cancel event', () => {
    const spy = jasmine.createSpy('cancel');
    component.cancel.subscribe(spy);
    component.onCancel();
    expect(spy).toHaveBeenCalled();
  });

  it('ngOnChanges should reset form when isOpen changes to false', () => {
    component.rejectForm.get('reason')!.setValue('Some reason');
    component.ngOnChanges({
      isOpen: new SimpleChange(true, false, false),
    });
    expect(component.rejectForm.get('reason')!.value).toBeNull();
  });
});
