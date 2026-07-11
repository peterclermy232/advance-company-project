import { ComponentFixture, TestBed } from '@angular/core/testing';
import { provideRouter } from '@angular/router';
import { FormsModule } from '@angular/forms';
import { of } from 'rxjs';
import { BeneficiaryListComponent } from './beneficiary-list.component';
import { BeneficiaryService } from '../../../core/services/beneficiary.service';
import { AuthService } from '../../../core/services/auth.service';
import { NotificationService } from '../../../core/services/notification.service';
import { Beneficiary } from '../../../core/models/beneficiary.model';

describe('BeneficiaryListComponent', () => {
  let fixture: ComponentFixture<BeneficiaryListComponent>;
  let component: BeneficiaryListComponent;

  const makeBeneficiary = (status: string): Beneficiary =>
    ({ uuid: status, name: 'Test', relation: 'child', status, verification_status: 'pending' } as any);

  beforeEach(async () => {
    const beneficiarySpy = jasmine.createSpyObj('BeneficiaryService', [
      'getBeneficiaries', 'deleteBeneficiary', 'markDeceased',
    ]);
    beneficiarySpy.getBeneficiaries.and.returnValue(of({ results: [] } as any));

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
      imports: [BeneficiaryListComponent, FormsModule],
      providers: [
        provideRouter([]),
        { provide: BeneficiaryService, useValue: beneficiarySpy },
        { provide: AuthService, useValue: authSpy },
        { provide: NotificationService, useValue: notifSpy },
      ],
    }).compileComponents();

    fixture = TestBed.createComponent(BeneficiaryListComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });

  it('should default sidebarOpen to true', () => {
    expect(component.sidebarOpen).toBeTrue();
  });

  it('should default activeTab to "active"', () => {
    expect(component.activeTab).toBe('active');
  });

  it('should default showDeleteModal to false', () => {
    expect(component.showDeleteModal).toBeFalse();
  });

  it('toggleSidebar should toggle sidebarOpen', () => {
    component.toggleSidebar();
    expect(component.sidebarOpen).toBeFalse();
  });
});
