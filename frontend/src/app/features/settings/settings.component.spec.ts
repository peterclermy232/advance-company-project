import { ComponentFixture, TestBed } from '@angular/core/testing';
import { ReactiveFormsModule, FormsModule } from '@angular/forms';
import { provideRouter } from '@angular/router';
import { of } from 'rxjs';
import { SettingsComponent } from './settings.component';
import { AuthService } from '../../core/services/auth.service';
import { NotificationService } from '../../core/services/notification.service';

describe('SettingsComponent', () => {
  let fixture: ComponentFixture<SettingsComponent>;
  let component: SettingsComponent;

  const mockUser = {
    id: 1, email: 'test@example.com', full_name: 'Test User',
    role: 'member', email_verified: true, phone_number: '+254700000000',
  };

  beforeEach(async () => {
    const authSpy = jasmine.createSpyObj('AuthService', [
      'isAdmin', 'logout', 'getCurrentUser', 'updateProfile',
      'changePassword', 'setup2FA', 'verify2FA', 'disable2FA', 'deleteAccount',
    ], { currentUser$: of(mockUser) });
    authSpy.isAdmin.and.returnValue(false);
    authSpy.getCurrentUser.and.returnValue(mockUser as any);

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
      imports: [SettingsComponent, ReactiveFormsModule, FormsModule],
      providers: [
        provideRouter([]),
        { provide: AuthService, useValue: authSpy },
        { provide: NotificationService, useValue: notifSpy },
      ],
    }).compileComponents();

    fixture = TestBed.createComponent(SettingsComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });

  it('should default sidebarOpen to true', () => {
    expect(component.sidebarOpen).toBeTrue();
  });

  it('should default showPasswordModal to false', () => {
    expect(component.showPasswordModal).toBeFalse();
  });

  it('should default show2FAModal to false', () => {
    expect(component.show2FAModal).toBeFalse();
  });

  it('profileForm should have the required controls', () => {
    ['full_name', 'email', 'phone_number', 'age', 'gender', 'marital_status', 'profession'].forEach(ctrl => {
      expect(component.profileForm.contains(ctrl)).toBeTrue();
    });
  });

  it('profileForm should be patched with currentUser data', () => {
    expect(component.profileForm.get('email')!.value).toBe('test@example.com');
    expect(component.profileForm.get('full_name')!.value).toBe('Test User');
  });

  it('passwordForm should have current_password, new_password, confirm_password', () => {
    ['current_password', 'new_password', 'confirm_password'].forEach(ctrl => {
      expect(component.passwordForm.contains(ctrl)).toBeTrue();
    });
  });

  it('twoFactorForm should have a code control', () => {
    expect(component.twoFactorForm.contains('code')).toBeTrue();
  });

  it('deleteAccountForm should have password and confirmation controls', () => {
    expect(component.deleteAccountForm.contains('password')).toBeTrue();
    expect(component.deleteAccountForm.contains('confirmation')).toBeTrue();
  });
});
