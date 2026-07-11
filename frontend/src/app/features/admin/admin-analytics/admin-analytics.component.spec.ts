import { ComponentFixture, TestBed } from '@angular/core/testing';
import { provideRouter } from '@angular/router';
import { FormsModule } from '@angular/forms';
import { of } from 'rxjs';
import { AdminAnalyticsComponent } from './admin-analytics.component';
import { AuthService } from '../../../core/services/auth.service';
import { ToastService } from '../../../core/services/toast.service';
import { AdminAnalyticsService } from '../../../core/services/admin-analytics.service';
import { NotificationService } from '../../../core/services/notification.service';

describe('AdminAnalyticsComponent', () => {
  let fixture: ComponentFixture<AdminAnalyticsComponent>;
  let component: AdminAnalyticsComponent;

  beforeEach(async () => {
    const analyticsSpy = jasmine.createSpyObj('AdminAnalyticsService', [
      'getOverview', 'getMonthlyTrends', 'getContributionDistribution',
      'getGrowthTimeline', 'getMemberActivity', 'getMemberAnalytics',
      'exportAnalytics',
    ]);
    analyticsSpy.getOverview.and.returnValue(of({} as any));
    analyticsSpy.getMonthlyTrends.and.returnValue(of({ results: [] } as any));
    analyticsSpy.getContributionDistribution.and.returnValue(of({ results: [] } as any));
    analyticsSpy.getGrowthTimeline.and.returnValue(of({ results: [] } as any));
    analyticsSpy.getMemberActivity.and.returnValue(of({ results: [] } as any));
    analyticsSpy.getMemberAnalytics.and.returnValue(of({ members: [] } as any));
    analyticsSpy.exportAnalytics.and.returnValue(of(new Blob() as any));

    const authSpy = jasmine.createSpyObj('AuthService', ['isAdmin', 'logout', 'getCurrentUser'], {
      currentUser$: of(null),
    });
    authSpy.isAdmin.and.returnValue(true);

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
      imports: [AdminAnalyticsComponent, FormsModule],
      providers: [
        provideRouter([]),
        { provide: AdminAnalyticsService, useValue: analyticsSpy },
        { provide: AuthService, useValue: authSpy },
        { provide: ToastService, useValue: toastSpy },
        { provide: NotificationService, useValue: notifSpy },
      ],
    }).compileComponents();

    fixture = TestBed.createComponent(AdminAnalyticsComponent);
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
