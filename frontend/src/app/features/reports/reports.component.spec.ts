import { ComponentFixture, TestBed } from '@angular/core/testing';
import { ReactiveFormsModule } from '@angular/forms';
import { provideRouter } from '@angular/router';
import { of } from 'rxjs';
import { ReportsComponent } from './reports.component';
import { AuthService } from '../../core/services/auth.service';
import { NotificationService } from '../../core/services/notification.service';
import { ReportService } from '../../core/services/report.service';
import { Report } from '../../core/models/report.model';

describe('ReportsComponent', () => {
  let fixture: ComponentFixture<ReportsComponent>;
  let component: ReportsComponent;
  let reportSpy: jasmine.SpyObj<ReportService>;
  let notifSpy: jasmine.SpyObj<NotificationService>;

  beforeEach(async () => {
    reportSpy = jasmine.createSpyObj('ReportService', [
      'getReports', 'generateFinancialReport', 'generateCompensatoryReport', 'generateActivityReport',
    ]);
    reportSpy.getReports.and.returnValue(of({ results: [] } as any));
    reportSpy.generateFinancialReport.and.returnValue(of({} as any));

    const authSpy = jasmine.createSpyObj('AuthService', ['isAdmin', 'logout', 'getCurrentUser'], {
      currentUser$: of(null),
    });
    authSpy.isAdmin.and.returnValue(false);

    notifSpy = jasmine.createSpyObj('NotificationService', [
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
      imports: [ReportsComponent, ReactiveFormsModule],
      providers: [
        provideRouter([]),
        { provide: AuthService, useValue: authSpy },
        { provide: NotificationService, useValue: notifSpy },
        { provide: ReportService, useValue: reportSpy },
      ],
    }).compileComponents();

    fixture = TestBed.createComponent(ReportsComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });

  it('should default activeTab to "FINANCIAL"', () => {
    expect(component.activeTab).toBe('FINANCIAL');
  });

  it('should default sidebarOpen to true', () => {
    expect(component.sidebarOpen).toBeTrue();
  });

  it('setActiveTab should update activeTab', () => {
    component.setActiveTab('COMPENSATORY');
    expect(component.activeTab).toBe('compensatory');
  });

  it('toggleSidebar should toggle sidebarOpen', () => {
    component.toggleSidebar();
    expect(component.sidebarOpen).toBeFalse();
  });

  it('getStatusClass should return green for "ready"', () => {
    expect(component.getStatusClass('ready')).toContain('green');
  });

  it('getStatusClass should return red for "failed"', () => {
    expect(component.getStatusClass('failed')).toContain('red');
  });

  it('getStatusClass should return fallback for unknown', () => {
    expect(component.getStatusClass('unknown')).toContain('gray');
  });

  it('canDownload should return true for ready report with file_url', () => {
    const report = { status: 'ready', file_url: 'https://example.com/file.pdf' } as Report;
    expect(component.canDownload(report)).toBeTrue();
  });

  it('canDownload should return false when file_url is missing', () => {
    const report = { status: 'ready', file_url: null } as any;
    expect(component.canDownload(report)).toBeFalse();
  });

  it('filterForm should have date_from and date_to controls', () => {
    expect(component.filterForm.contains('date_from')).toBeTrue();
    expect(component.filterForm.contains('date_to')).toBeTrue();
  });
});
