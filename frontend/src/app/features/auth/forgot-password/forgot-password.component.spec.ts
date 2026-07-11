import { ComponentFixture, TestBed } from '@angular/core/testing';
import { provideRouter } from '@angular/router';
import { provideHttpClient } from '@angular/common/http';
import { provideHttpClientTesting } from '@angular/common/http/testing';
import { of } from 'rxjs';
import { ForgotPasswordComponent } from './forgot-password.component';
import { AuthService } from '../../../core/services/auth.service';
import { NotificationService } from '../../../core/services/notification.service';

describe('ForgotPasswordComponent', () => {
  let component: ForgotPasswordComponent;
  let fixture: ComponentFixture<ForgotPasswordComponent>;

  beforeEach(async () => {
    const authSpy = jasmine.createSpyObj('AuthService', ['forgotPassword', 'isAdmin', 'logout'], {
      currentUser$: of(null),
    });
    authSpy.forgotPassword.and.returnValue(of({} as any));

    const notifSpy = jasmine.createSpyObj('NotificationService', [
      'success', 'error', 'warning', 'info',
    ], { notifications$: of([]), unreadCount$: of(0) });

    await TestBed.configureTestingModule({
      imports: [ForgotPasswordComponent],
      providers: [
        provideRouter([]),
        provideHttpClient(),
        provideHttpClientTesting(),
        { provide: AuthService, useValue: authSpy },
        { provide: NotificationService, useValue: notifSpy },
      ],
    }).compileComponents();

    fixture = TestBed.createComponent(ForgotPasswordComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });

  it('should start with emailSent false', () => {
    expect(component.emailSent).toBeFalse();
  });

  it('should have an email control', () => {
    expect(component.forgotPasswordForm.contains('email')).toBeTrue();
  });

  it('email should be invalid when empty', () => {
    component.forgotPasswordForm.get('email')!.setValue('');
    expect(component.forgotPasswordForm.get('email')!.valid).toBeFalse();
  });

  it('email should be valid with proper email', () => {
    component.forgotPasswordForm.get('email')!.setValue('test@example.com');
    expect(component.forgotPasswordForm.get('email')!.valid).toBeTrue();
  });

  it('resetForm should set emailSent to false', () => {
    component.emailSent = true;
    component.resetForm();
    expect(component.emailSent).toBeFalse();
  });
});
