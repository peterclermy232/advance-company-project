import { ComponentFixture, TestBed } from '@angular/core/testing';
import { provideRouter } from '@angular/router';
import { FormsModule } from '@angular/forms';
import { of } from 'rxjs';
import { ApplicationListComponent } from './application-list.component';
import { ApplicationService } from '../../../core/services/application.service';
import { AuthService } from '../../../core/services/auth.service';
import { NotificationService } from '../../../core/services/notification.service';

describe('ApplicationListComponent', () => {
  let fixture: ComponentFixture<ApplicationListComponent>;
  let component: ApplicationListComponent;

  beforeEach(async () => {
    const applicationSpy = jasmine.createSpyObj('ApplicationService', [
      'getApplications', 'approveApplication', 'rejectApplication',
    ]);
    applicationSpy.getApplications.and.returnValue(of([] as any));

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
      imports: [ApplicationListComponent, FormsModule],
      providers: [
        provideRouter([]),
        { provide: ApplicationService, useValue: applicationSpy },
        { provide: AuthService, useValue: authSpy },
        { provide: NotificationService, useValue: notifSpy },
      ],
    }).compileComponents();

    fixture = TestBed.createComponent(ApplicationListComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });

  it('should default sidebarOpen to true', () => {
    expect(component.sidebarOpen).toBeTrue();
  });

  it('should default showActionModal to false', () => {
    expect(component.showActionModal).toBeFalse();
  });

  it('should default applications to empty array after load', () => {
    expect(component.applications).toEqual([]);
  });

  it('toggleSidebar should toggle sidebarOpen', () => {
    component.toggleSidebar();
    expect(component.sidebarOpen).toBeFalse();
  });

  it('openActionModal should set selectedApplication and actionType', () => {
    const app = { uuid: 'abc', application_type: 'loan' } as any;
    component.openActionModal(app, 'approve');
    expect(component.selectedApplication).toBe(app);
    expect(component.actionType).toBe('approve');
    expect(component.showActionModal).toBeTrue();
  });
});
