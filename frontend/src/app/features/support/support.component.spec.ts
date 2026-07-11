import { ComponentFixture, TestBed, fakeAsync, tick } from '@angular/core/testing';
import { ReactiveFormsModule } from '@angular/forms';
import { provideRouter } from '@angular/router';
import { of } from 'rxjs';
import { SupportComponent } from './support.component';
import { AuthService } from '../../core/services/auth.service';
import { NotificationService } from '../../core/services/notification.service';

describe('SupportComponent', () => {
  let fixture: ComponentFixture<SupportComponent>;
  let component: SupportComponent;
  let notifSpy: jasmine.SpyObj<NotificationService>;

  beforeEach(async () => {
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
      imports: [SupportComponent, ReactiveFormsModule],
      providers: [
        provideRouter([]),
        { provide: AuthService, useValue: authSpy },
        { provide: NotificationService, useValue: notifSpy },
      ],
    }).compileComponents();

    fixture = TestBed.createComponent(SupportComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });

  it('should have a contactForm with subject and message controls', () => {
    expect(component.contactForm.contains('subject')).toBeTrue();
    expect(component.contactForm.contains('message')).toBeTrue();
  });

  it('should default sidebarOpen to true', () => {
    expect(component.sidebarOpen).toBeTrue();
  });

  it('toggleSidebar should toggle sidebarOpen', () => {
    component.toggleSidebar();
    expect(component.sidebarOpen).toBeFalse();
  });

  it('faqs array should not be empty', () => {
    expect(component.faqs.length).toBeGreaterThan(0);
  });

  it('each FAQ should have a question and answer', () => {
    component.faqs.forEach(faq => {
      expect(faq.question).toBeTruthy();
      expect(faq.answer).toBeTruthy();
    });
  });

  it('onSubmitContact with invalid form should not call notificationService', () => {
    component.onSubmitContact();
    expect(notifSpy.success).not.toHaveBeenCalled();
  });

  it('onSubmitContact with valid form should show success toast', fakeAsync(() => {
    component.contactForm.setValue({ subject: 'Help needed', message: 'I need help with deposits' });
    component.onSubmitContact();
    tick(1500);
    expect(notifSpy.success).toHaveBeenCalled();
  }));

  it('isSubmitting should be false initially', () => {
    expect(component.isSubmitting).toBeFalse();
  });
});
