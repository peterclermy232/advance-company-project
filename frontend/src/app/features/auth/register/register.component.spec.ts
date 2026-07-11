import { Component } from '@angular/core';
import { ComponentFixture, TestBed, fakeAsync, tick } from '@angular/core/testing';
import { ReactiveFormsModule } from '@angular/forms';
import { provideRouter } from '@angular/router';
import { of, throwError } from 'rxjs';

@Component({ standalone: true, template: '' })
class StubComponent {}
import { RegisterComponent } from './register.component';
import { AuthService } from '../../../core/services/auth.service';
import { NotificationService } from '../../../core/services/notification.service';

describe('RegisterComponent', () => {
  let fixture: ComponentFixture<RegisterComponent>;
  let component: RegisterComponent;
  let authSpy: jasmine.SpyObj<AuthService>;
  let notifSpy: jasmine.SpyObj<NotificationService>;

  beforeEach(async () => {
    authSpy = jasmine.createSpyObj('AuthService', ['register'], {
      currentUser$: of(null),
    });
    notifSpy = jasmine.createSpyObj('NotificationService', [
      'success', 'error', 'warning', 'info', 'loading',
      'refresh', 'initialize', 'getRecentNotifications',
      'markAsRead', 'markAllAsRead', 'clearAll',
    ], { notifications$: of([]), unreadCount$: of(0) });
    notifSpy.refresh.and.returnValue(undefined as any);
    notifSpy.initialize.and.returnValue(undefined as any);
    notifSpy.getRecentNotifications.and.returnValue(of({ results: [], count: 0 } as any));

    await TestBed.configureTestingModule({
      imports: [RegisterComponent, ReactiveFormsModule],
      providers: [
        provideRouter([{ path: 'auth/verify-email', component: StubComponent }]),
        { provide: AuthService, useValue: authSpy },
        { provide: NotificationService, useValue: notifSpy },
      ],
    }).compileComponents();

    fixture = TestBed.createComponent(RegisterComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });

  it('should initialise with an invalid form', () => {
    expect(component.registerForm.valid).toBeFalse();
  });

  it('should have all required form controls', () => {
    ['full_name', 'email', 'phone_number', 'password', 'password_confirm'].forEach(ctrl => {
      expect(component.registerForm.contains(ctrl)).toBeTrue();
    });
  });

  it('should default showPassword to false', () => {
    expect(component.showPassword).toBeFalse();
  });

  it('should default showConfirmPassword to false', () => {
    expect(component.showConfirmPassword).toBeFalse();
  });

  it('togglePassword should toggle showPassword', () => {
    component.togglePassword();
    expect(component.showPassword).toBeTrue();
    component.togglePassword();
    expect(component.showPassword).toBeFalse();
  });

  it('toggleConfirmPassword should toggle showConfirmPassword', () => {
    component.toggleConfirmPassword();
    expect(component.showConfirmPassword).toBeTrue();
  });

  it('passwordHasUpperCase should return false for lowercase-only', () => {
    component.registerForm.get('password')!.setValue('lowercase');
    expect(component.passwordHasUpperCase()).toBeFalse();
  });

  it('passwordHasUpperCase should return true when uppercase present', () => {
    component.registerForm.get('password')!.setValue('Password1!');
    expect(component.passwordHasUpperCase()).toBeTrue();
  });

  it('passwordHasNumber should return true when digit present', () => {
    component.registerForm.get('password')!.setValue('Password1!');
    expect(component.passwordHasNumber()).toBeTrue();
  });

  it('passwordHasSpecialChar should return true when special char present', () => {
    component.registerForm.get('password')!.setValue('Password1!');
    expect(component.passwordHasSpecialChar()).toBeTrue();
  });

  it('passwordMinLength should return true when >= 12 chars', () => {
    component.registerForm.get('password')!.setValue('Str0ngP@ssword!');
    expect(component.passwordMinLength()).toBeTrue();
  });

  it('passwordMinLength should return false when < 12 chars', () => {
    component.registerForm.get('password')!.setValue('Short1!');
    expect(component.passwordMinLength()).toBeFalse();
  });

  it('onSubmit with invalid form should mark all touched', () => {
    component.onSubmit();
    expect(component.registerForm.touched).toBeTrue();
  });

  it('onSubmit with invalid form should not call authService.register', () => {
    component.onSubmit();
    expect(authSpy.register).not.toHaveBeenCalled();
  });

  it('onSubmit with valid form should call authService.register', fakeAsync(() => {
    authSpy.register.and.returnValue(of({ message: 'Success', toast_type: 'success' } as any));
    component.registerForm.setValue({
      full_name: 'Test User',
      email: 'test@example.com',
      phone_number: '+254712345678',
      password: 'Str0ngP@ssword!',
      password_confirm: 'Str0ngP@ssword!',
    });
    component.onSubmit();
    tick();
    expect(authSpy.register).toHaveBeenCalled();
  }));

  it('onSubmit failure should call notifSpy.error', fakeAsync(() => {
    authSpy.register.and.returnValue(throwError(() => ({ error: { message: 'Email taken' } })));
    component.registerForm.setValue({
      full_name: 'Test User',
      email: 'test@example.com',
      phone_number: '+254712345678',
      password: 'Str0ngP@ssword!',
      password_confirm: 'Str0ngP@ssword!',
    });
    component.onSubmit();
    tick();
    expect(notifSpy.error).toHaveBeenCalled();
  }));
});
