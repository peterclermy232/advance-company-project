import { ComponentFixture, TestBed } from '@angular/core/testing';
import { provideRouter } from '@angular/router';
import { of } from 'rxjs';
import { NotificationsComponent } from './notifications.component';
import { AuthService } from '../../core/services/auth.service';
import { NotificationService, AppNotification } from '../../core/services/notification.service';

describe('NotificationsComponent', () => {
  let fixture: ComponentFixture<NotificationsComponent>;
  let component: NotificationsComponent;
  let notifSpy: jasmine.SpyObj<NotificationService>;

  beforeEach(async () => {
    const authSpy = jasmine.createSpyObj('AuthService', ['isAdmin', 'logout', 'getCurrentUser'], {
      currentUser$: of({ id: 1, email: 'test@example.com', full_name: 'Test User', role: 'member' }),
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
      imports: [NotificationsComponent],
      providers: [
        provideRouter([]),
        { provide: AuthService, useValue: authSpy },
        { provide: NotificationService, useValue: notifSpy },
      ],
    }).compileComponents();

    fixture = TestBed.createComponent(NotificationsComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });

  it('should default sidebarOpen to true', () => {
    expect(component.sidebarOpen).toBeTrue();
  });

  it('toggleSidebar should toggle sidebarOpen', () => {
    component.toggleSidebar();
    expect(component.sidebarOpen).toBeFalse();
  });

  it('getIconClass should return blue class for "deposit_created"', () => {
    expect(component.getIconClass('deposit_created')).toContain('blue');
  });

  it('getIconClass should return green class for "deposit_approved"', () => {
    expect(component.getIconClass('deposit_approved')).toContain('green');
  });

  it('getIconClass should return default class for unknown type', () => {
    expect(component.getIconClass('unknown')).toContain('gray');
  });

  it('markAllAsRead should call service', () => {
    component.markAllAsRead();
    expect(notifSpy.markAllAsRead).toHaveBeenCalled();
  });
});
