import { ComponentFixture, TestBed } from '@angular/core/testing';
import { provideRouter } from '@angular/router';
import { of } from 'rxjs';
import { HeaderComponent } from './header.component';
import { AuthService } from '../../../core/services/auth.service';
import { NotificationService } from '../../../core/services/notification.service';

describe('HeaderComponent', () => {
  let fixture: ComponentFixture<HeaderComponent>;
  let component: HeaderComponent;
  let authSpy: jasmine.SpyObj<AuthService>;
  let notifSpy: jasmine.SpyObj<NotificationService>;

  const mockUser = {
    id: 1, email: 'test@example.com', full_name: 'Test User', role: 'member', email_verified: true,
  };

  beforeEach(async () => {
    authSpy = jasmine.createSpyObj('AuthService', ['logout', 'isAdmin', 'getCurrentUser'], {
      currentUser$: of(mockUser),
    });
    authSpy.isAdmin.and.returnValue(false);
    authSpy.getCurrentUser.and.returnValue(mockUser as any);

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
      imports: [HeaderComponent],
      providers: [
        provideRouter([]),
        { provide: AuthService, useValue: authSpy },
        { provide: NotificationService, useValue: notifSpy },
      ],
    }).compileComponents();

    fixture = TestBed.createComponent(HeaderComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });

  it('should subscribe to currentUser$ on ngOnInit', () => {
    expect(component.currentUser).toEqual(mockUser as any);
  });

  it('logout should call authService.logout', () => {
    component.logout();
    expect(authSpy.logout).toHaveBeenCalled();
  });

  it('onToggleSidebar should emit toggleSidebar event', () => {
    const spy = jasmine.createSpy('toggleSidebar');
    component.toggleSidebar.subscribe(spy);
    component.onToggleSidebar();
    expect(spy).toHaveBeenCalled();
  });
});
