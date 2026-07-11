import { ComponentFixture, TestBed } from '@angular/core/testing';
import { provideRouter } from '@angular/router';
import { of } from 'rxjs';
import { NotificationDropdownComponent } from './notification-dropdown.component';
import { NotificationService, AppNotification } from '../../../core/services/notification.service';

describe('NotificationDropdownComponent', () => {
  let fixture: ComponentFixture<NotificationDropdownComponent>;
  let component: NotificationDropdownComponent;
  let notifSpy: jasmine.SpyObj<NotificationService>;

  const mockNotification: AppNotification = {
    uuid: 'n1',
    title: 'Test',
    message: 'Test message',
    notification_type: 'deposit_created',
    is_read: false,
    created_at: '2025-01-01T00:00:00Z',
    time_ago: '1 hour ago',
  } as any;

  beforeEach(async () => {
    notifSpy = jasmine.createSpyObj('NotificationService', [
      'refresh', 'initialize', 'getRecentNotifications',
      'markAsRead', 'markAllAsRead', 'clearAll',
      'success', 'error', 'warning', 'info', 'loading',
    ], { notifications$: of([mockNotification]), unreadCount$: of(1) });
    notifSpy.refresh.and.returnValue(undefined as any);
    notifSpy.initialize.and.returnValue(undefined as any);
    notifSpy.getRecentNotifications.and.returnValue(of({ results: [mockNotification], count: 1 } as any));
    notifSpy.markAsRead.and.returnValue(of({} as any));
    notifSpy.markAllAsRead.and.returnValue(of({} as any));
    notifSpy.clearAll.and.returnValue(of({} as any));

    await TestBed.configureTestingModule({
      imports: [NotificationDropdownComponent],
      providers: [
        provideRouter([]),
        { provide: NotificationService, useValue: notifSpy },
      ],
    }).compileComponents();

    fixture = TestBed.createComponent(NotificationDropdownComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });

  it('should subscribe to notifications$ on ngOnInit', () => {
    expect(component.notifications).toContain(mockNotification);
  });

  it('should subscribe to unreadCount$ on ngOnInit', () => {
    expect(component.unreadCount).toBe(1);
  });

  it('toggleDropdown should toggle isOpen', () => {
    expect(component.isOpen).toBeFalse();
    component.toggleDropdown();
    expect(component.isOpen).toBeTrue();
    component.toggleDropdown();
    expect(component.isOpen).toBeFalse();
  });

  it('closeDropdown should set isOpen to false', () => {
    component.isOpen = true;
    component.closeDropdown();
    expect(component.isOpen).toBeFalse();
  });

  it('markAllAsRead should call service', () => {
    component.markAllAsRead();
    expect(notifSpy.markAllAsRead).toHaveBeenCalled();
  });

  it('getIconClass should return a class string for "deposit_approved"', () => {
    expect(component.getIconClass('deposit_approved')).toContain('green');
  });

  it('getIconClass should return default class for unknown type', () => {
    expect(component.getIconClass('unknown_type')).toContain('gray');
  });

  it('ngOnDestroy should unsubscribe all subscriptions', () => {
    expect(() => component.ngOnDestroy()).not.toThrow();
  });
});
