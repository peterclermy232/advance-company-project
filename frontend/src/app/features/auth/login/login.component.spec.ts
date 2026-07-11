import { Component } from '@angular/core';
import { ComponentFixture, TestBed, fakeAsync, tick, flush } from '@angular/core/testing';
import { ReactiveFormsModule } from '@angular/forms';
import { provideRouter } from '@angular/router';
import { of, throwError } from 'rxjs';

@Component({ standalone: true, template: '' })
class StubComponent {}
import { LoginComponent } from './login.component';
import { AuthService } from '../../../core/services/auth.service';
import { ToastService } from '../../../core/services/toast.service';

describe('LoginComponent', () => {
  let component: LoginComponent;
  let fixture: ComponentFixture<LoginComponent>;
  let authSpy: jasmine.SpyObj<AuthService>;
  let toastSpy: jasmine.SpyObj<ToastService>;

  const mockLoginResponse = {
    success: true,
    message: 'Login successful',
    toast_type: 'success',
    data: {
      user: { id: 1, email: 'test@example.com', full_name: 'Test User', role: 'member', email_verified: true },
      tokens: { access: 'access-token', refresh: 'refresh-token' },
    },
  };

  beforeEach(async () => {
    authSpy = jasmine.createSpyObj('AuthService', ['login'], {
      currentUser$: of(null),
    });
    toastSpy = jasmine.createSpyObj('ToastService', [
      'success',
      'error',
      'warning',
      'info',
    ]);

    await TestBed.configureTestingModule({
      imports: [LoginComponent, ReactiveFormsModule],
      providers: [
        provideRouter([
          { path: 'dashboard', component: StubComponent },
          { path: 'auth/login', component: StubComponent },
          { path: 'auth/verify-email', component: StubComponent },
        ]),
        { provide: AuthService, useValue: authSpy },
        { provide: ToastService, useValue: toastSpy },
      ],
    }).compileComponents();

    fixture = TestBed.createComponent(LoginComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  // ── Component creation ─────────────────────────────────────────────────────

  it('should create', () => {
    expect(component).toBeTruthy();
  });

  // ── Form initialisation ────────────────────────────────────────────────────

  it('should initialise with an invalid form', () => {
    expect(component.loginForm.valid).toBeFalse();
  });

  it('should have email, password and remember controls', () => {
    expect(component.loginForm.contains('email')).toBeTrue();
    expect(component.loginForm.contains('password')).toBeTrue();
    expect(component.loginForm.contains('remember')).toBeTrue();
  });

  // ── Email validation ───────────────────────────────────────────────────────

  it('should invalidate a badly formatted email', () => {
    component.loginForm.get('email')!.setValue('not-an-email');
    expect(component.loginForm.get('email')!.valid).toBeFalse();
  });

  it('should accept a valid email', () => {
    component.loginForm.get('email')!.setValue('valid@example.com');
    expect(component.loginForm.get('email')!.valid).toBeTrue();
  });

  // ── Password validation ────────────────────────────────────────────────────

  it('should reject a password shorter than 6 characters', () => {
    component.loginForm.get('password')!.setValue('abc');
    expect(component.loginForm.get('password')!.valid).toBeFalse();
  });

  it('should accept a password of 6 or more characters', () => {
    component.loginForm.get('password')!.setValue('abcdefg');
    expect(component.loginForm.get('password')!.valid).toBeTrue();
  });

  // ── Password toggle ────────────────────────────────────────────────────────

  it('showPassword should default to false', () => {
    expect(component.showPassword).toBeFalse();
  });

  it('should toggle showPassword', () => {
    component.showPassword = true;
    expect(component.showPassword).toBeTrue();
  });

  // ── Submit guard ───────────────────────────────────────────────────────────

  it('should show warning toast when submitting an invalid form', () => {
    component.onSubmit();
    expect(toastSpy.warning).toHaveBeenCalled();
  });

  it('should not call authService.login when form is invalid', () => {
    component.onSubmit();
    expect(authSpy.login).not.toHaveBeenCalled();
  });

  // ── Successful login ───────────────────────────────────────────────────────

  it('should call authService.login with email and password', fakeAsync(() => {
    authSpy.login.and.returnValue(of(mockLoginResponse as any));
    component.loginForm.setValue({
      email: 'test@example.com',
      password: 'TestPass1',
      remember: false,
    });

    component.onSubmit();
    tick(700);

    expect(authSpy.login).toHaveBeenCalledWith({
      email: 'test@example.com',
      password: 'TestPass1',
    });
  }));

  it('should set isLoading to false after login completes', fakeAsync(() => {
    authSpy.login.and.returnValue(of(mockLoginResponse as any));
    component.loginForm.setValue({
      email: 'test@example.com',
      password: 'TestPass1',
      remember: false,
    });

    component.onSubmit();
    tick(700);

    expect(component.isLoading).toBeFalse();
  }));

  // ── 2FA flow ───────────────────────────────────────────────────────────────

  it('should open the 2FA modal when backend returns requires_2fa', fakeAsync(() => {
    authSpy.login.and.returnValue(
      of({ ...mockLoginResponse, data: { ...mockLoginResponse.data, requires_2fa: true } } as any)
    );
    component.loginForm.setValue({
      email: 'test@example.com',
      password: 'TestPass1',
      remember: false,
    });

    component.onSubmit();
    flush();

    expect(component.show2FAModal).toBeTrue();
  }));

  // ── Failed login ───────────────────────────────────────────────────────────

  it('should show error toast on failed login', fakeAsync(() => {
    authSpy.login.and.returnValue(
      throwError(() => ({
        status: 401,
        error: { message: 'Invalid credentials', toast_type: 'error' },
      }))
    );
    component.loginForm.setValue({
      email: 'test@example.com',
      password: 'WrongPass1',
      remember: false,
    });

    component.onSubmit();
    tick();

    expect(toastSpy.error).toHaveBeenCalled();
  }));

  it('should set isLoading to false after a failed login', fakeAsync(() => {
    authSpy.login.and.returnValue(throwError(() => ({ status: 401 })));
    component.loginForm.setValue({
      email: 'test@example.com',
      password: 'WrongPass1',
      remember: false,
    });

    component.onSubmit();
    tick();

    expect(component.isLoading).toBeFalse();
  }));
});
