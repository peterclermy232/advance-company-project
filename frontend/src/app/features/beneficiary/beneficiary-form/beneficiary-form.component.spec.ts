import { ComponentFixture, TestBed } from '@angular/core/testing';
import { ReactiveFormsModule } from '@angular/forms';
import { provideRouter } from '@angular/router';
import { ActivatedRoute } from '@angular/router';
import { of } from 'rxjs';
import { BeneficiaryFormComponent } from './beneficiary-form.component';
import { BeneficiaryService } from '../../../core/services/beneficiary.service';
import { AuthService } from '../../../core/services/auth.service';
import { NotificationService } from '../../../core/services/notification.service';

describe('BeneficiaryFormComponent', () => {
  let fixture: ComponentFixture<BeneficiaryFormComponent>;
  let component: BeneficiaryFormComponent;

  beforeEach(async () => {
    const beneficiarySpy = jasmine.createSpyObj('BeneficiaryService', [
      'getBeneficiary', 'getBeneficiaries', 'createBeneficiary', 'updateBeneficiary', 'getStatistics',
    ]);
    beneficiarySpy.getBeneficiary.and.returnValue(of({} as any));
    beneficiarySpy.getBeneficiaries.and.returnValue(of({ results: [], count: 0 } as any));
    beneficiarySpy.getStatistics.and.returnValue(of({ total_allocated: 0 } as any));

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
      imports: [BeneficiaryFormComponent, ReactiveFormsModule],
      providers: [
        provideRouter([]),
        { provide: ActivatedRoute, useValue: { params: of({}) } },
        { provide: BeneficiaryService, useValue: beneficiarySpy },
        { provide: AuthService, useValue: authSpy },
        { provide: NotificationService, useValue: notifSpy },
      ],
    }).compileComponents();

    fixture = TestBed.createComponent(BeneficiaryFormComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });

  it('should default isEditMode to false', () => {
    expect(component.isEditMode).toBeFalse();
  });

  it('should default sidebarOpen to true', () => {
    expect(component.sidebarOpen).toBeTrue();
  });

  it('beneficiaryForm should have required controls', () => {
    ['name', 'relation', 'age', 'gender', 'percentage_allocation'].forEach(ctrl => {
      expect(component.beneficiaryForm.contains(ctrl)).toBeTrue();
    });
  });

  it('name should be required and min 3 chars', () => {
    component.beneficiaryForm.get('name')!.setValue('AB');
    expect(component.beneficiaryForm.get('name')!.valid).toBeFalse();
    component.beneficiaryForm.get('name')!.setValue('Alice');
    expect(component.beneficiaryForm.get('name')!.valid).toBeTrue();
  });

  it('percentage_allocation should accept valid value', () => {
    component.beneficiaryForm.get('percentage_allocation')!.setValue(50);
    expect(component.beneficiaryForm.get('percentage_allocation')!.valid).toBeTrue();
  });

  it('percentage_allocation should reject value > 100', () => {
    component.beneficiaryForm.get('percentage_allocation')!.setValue(101);
    expect(component.beneficiaryForm.get('percentage_allocation')!.valid).toBeFalse();
  });
});
