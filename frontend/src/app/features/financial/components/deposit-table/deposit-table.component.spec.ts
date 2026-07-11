import { ComponentFixture, TestBed } from '@angular/core/testing';
import { DepositTableComponent } from './deposit-table.component';
import { Deposit } from '../../../../core/models/financial.model';

describe('DepositTableComponent', () => {
  let fixture: ComponentFixture<DepositTableComponent>;
  let component: DepositTableComponent;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [DepositTableComponent],
    }).compileComponents();

    fixture = TestBed.createComponent(DepositTableComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });

  it('should default deposits to empty array', () => {
    expect(component.deposits).toEqual([]);
  });

  it('should default filterStatus to "pending"', () => {
    expect(component.filterStatus).toBe('pending');
  });

  it('should default isAdmin to false', () => {
    expect(component.isAdmin).toBeFalse();
  });

  it('getStatusClass should return green class for "completed"', () => {
    expect(component.getStatusClass('completed')).toContain('green');
  });

  it('getStatusClass should return yellow class for "pending"', () => {
    expect(component.getStatusClass('pending')).toContain('yellow');
  });

  it('getStatusClass should return red class for "failed"', () => {
    expect(component.getStatusClass('failed')).toContain('red');
  });

  it('getStatusClass should return fallback for unknown status', () => {
    expect(component.getStatusClass('unknown')).toContain('gray');
  });

  it('getStatusLabel should return "Approved" for "completed"', () => {
    expect(component.getStatusLabel('completed')).toBe('Approved');
  });

  it('getStatusLabel should return "Rejected" for "failed"', () => {
    expect(component.getStatusLabel('failed')).toBe('Rejected');
  });

  it('onApprove should emit the deposit', () => {
    const spy = jasmine.createSpy('approve');
    component.approve.subscribe(spy);
    const deposit = { uuid: 'abc' } as Deposit;
    component.onApprove(deposit);
    expect(spy).toHaveBeenCalledWith(deposit);
  });

  it('onReject should emit the deposit', () => {
    const spy = jasmine.createSpy('reject');
    component.reject.subscribe(spy);
    const deposit = { uuid: 'def' } as Deposit;
    component.onReject(deposit);
    expect(spy).toHaveBeenCalledWith(deposit);
  });

  it('onFilterChange should emit the new status', () => {
    const spy = jasmine.createSpy('filterChange');
    component.filterChange.subscribe(spy);
    component.onFilterChange('completed');
    expect(spy).toHaveBeenCalledWith('completed');
  });
});
