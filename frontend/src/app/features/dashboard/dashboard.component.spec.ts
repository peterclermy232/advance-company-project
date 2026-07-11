import { ComponentFixture, TestBed } from '@angular/core/testing';
import { provideRouter } from '@angular/router';
import { of } from 'rxjs';
import { DashboardComponent } from './dashboard.component';
import { AuthService } from '../../core/services/auth.service';
import { NotificationService } from '../../core/services/notification.service';
import { ApiService } from '../../core/services/api.service';
import { FinancialService } from '../../core/services/financial.service';

describe('DashboardComponent', () => {
  let fixture: ComponentFixture<DashboardComponent>;
  let component: DashboardComponent;

  beforeEach(async () => {
    const apiSpy = jasmine.createSpyObj('ApiService', ['get', 'post']);
    apiSpy.get.and.returnValue(of({} as any));

    const financialSpy = jasmine.createSpyObj('FinancialService', ['getMonthlySummary']);
    financialSpy.getMonthlySummary.and.returnValue(of({ results: [] } as any));

    const authSpy = jasmine.createSpyObj('AuthService', ['isAdmin', 'logout', 'getCurrentUser'], {
      currentUser$: of({ id: 1, email: 'test@example.com', full_name: 'Test User', role: 'member' }),
    });
    authSpy.isAdmin.and.returnValue(false);
    authSpy.getCurrentUser.and.returnValue({ id: 1, email: 'test@example.com', full_name: 'Test User' } as any);

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
      imports: [DashboardComponent],
      providers: [
        provideRouter([]),
        { provide: ApiService, useValue: apiSpy },
        { provide: FinancialService, useValue: financialSpy },
        { provide: AuthService, useValue: authSpy },
        { provide: NotificationService, useValue: notifSpy },
      ],
    }).compileComponents();

    fixture = TestBed.createComponent(DashboardComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });

  it('should default sidebarOpen to true', () => {
    expect(component.sidebarOpen).toBeTrue();
  });

  it('should default selectedRange to 6', () => {
    expect(component.selectedRange).toBe(6);
  });

  it('visibleData should return empty when allChartData is empty', () => {
    component.allChartData = [];
    expect(component.visibleData).toEqual([]);
  });

  it('visibleData should return last N entries matching selectedRange', () => {
    component.allChartData = [1, 2, 3, 4, 5, 6, 7, 8].map(m => ({
      month: m, year: 2025, total_deposits: m * 1000, count: 1,
    }));
    component.selectedRange = 3;
    expect(component.visibleData.length).toBe(3);
    expect(component.visibleData[0].month).toBe(6);
  });

  it('totalVisibleContributions should sum total_deposits', () => {
    component.allChartData = [
      { month: 1, year: 2025, total_deposits: 5000, count: 1 },
      { month: 2, year: 2025, total_deposits: 3000, count: 1 },
    ];
    component.selectedRange = 2;
    expect(component.totalVisibleContributions).toBe(8000);
  });

  it('chartHasData should return false when visibleData is empty', () => {
    component.allChartData = [];
    expect(component.chartHasData).toBeFalse();
  });

  it('chartHasData should return true when visibleData has items', () => {
    component.allChartData = [{ month: 1, year: 2025, total_deposits: 5000, count: 1 }];
    component.selectedRange = 1;
    expect(component.chartHasData).toBeTrue();
  });

  it('getBarHeightPct should return at least 2', () => {
    component.allChartData = [{ month: 1, year: 2025, total_deposits: 0, count: 0 }];
    component.selectedRange = 1;
    expect(component.getBarHeightPct(0)).toBeGreaterThanOrEqual(2);
  });

  it('getStatusFromNotificationType should return "success" for "approved"', () => {
    expect(component.getStatusFromNotificationType('deposit_approved')).toBe('success');
  });

  it('getStatusFromNotificationType should return "rejected" for "rejected"', () => {
    expect(component.getStatusFromNotificationType('deposit_rejected')).toBe('rejected');
  });

  it('getStatusFromNotificationType should return "pending" for others', () => {
    expect(component.getStatusFromNotificationType('deposit_created')).toBe('pending');
  });

  it('extractAmountOrDetail should extract KES amount from message', () => {
    expect(component.extractAmountOrDetail('Deposit of KES 20,000 received')).toBe('KES 20,000');
  });
});
