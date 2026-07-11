import { ComponentFixture, TestBed } from '@angular/core/testing';
import { ReactiveFormsModule } from '@angular/forms';
import { provideRouter } from '@angular/router';
import { of } from 'rxjs';
import { ApplicationFormComponent } from './application-form.component';
import { ApplicationService } from '../../../core/services/application.service';
import { AuthService } from '../../../core/services/auth.service';
import { NotificationService } from '../../../core/services/notification.service';

describe('ApplicationFormComponent', () => {
  let fixture: ComponentFixture<ApplicationFormComponent>;
  let component: ApplicationFormComponent;

  beforeEach(async () => {
    const applicationSpy = jasmine.createSpyObj('ApplicationService', [
      'getChoices', 'submitApplication',
    ]);
    applicationSpy.getChoices.and.returnValue(of({
      application_types: [
        { value: 'loan', label: 'Loan', description: 'Apply for a loan' },
      ],
      status_choices: [],
    } as any));

    const authSpy = jasmine.createSpyObj('AuthService', ['isAdmin', 'logout', 'getCurrentUser'], {
      currentUser$: of({ id: 1, email: 'test@example.com', full_name: 'Test User', role: 'member' }),
    });
    authSpy.isAdmin.and.returnValue(false);
    authSpy.getCurrentUser.and.returnValue({ id: 1, full_name: 'Test User' } as any);

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
      imports: [ApplicationFormComponent, ReactiveFormsModule],
      providers: [
        provideRouter([]),
        { provide: ApplicationService, useValue: applicationSpy },
        { provide: AuthService, useValue: authSpy },
        { provide: NotificationService, useValue: notifSpy },
      ],
    }).compileComponents();

    fixture = TestBed.createComponent(ApplicationFormComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });

  it('applicationForm should have application_type and reason controls', () => {
    expect(component.applicationForm.contains('application_type')).toBeTrue();
    expect(component.applicationForm.contains('reason')).toBeTrue();
  });

  it('reason should require minLength 20', () => {
    component.applicationForm.get('reason')!.setValue('short');
    expect(component.applicationForm.get('reason')!.valid).toBeFalse();
    component.applicationForm.get('reason')!.setValue('This is a long enough reason for the application');
    expect(component.applicationForm.get('reason')!.valid).toBeTrue();
  });

  it('selectedTypeDescription should return empty when no type selected', () => {
    component.applicationForm.get('application_type')!.setValue('');
    expect(component.selectedTypeDescription).toBe('');
  });

  it('selectedTypeDescription should return description for known type', () => {
    component.applicationForm.get('application_type')!.setValue('loan');
    expect(component.selectedTypeDescription).toBe('Apply for a loan');
  });

  it('sidebarOpen should default to true', () => {
    expect(component.sidebarOpen).toBeTrue();
  });

  it('isSubmitting should default to false', () => {
    expect(component.isSubmitting).toBeFalse();
  });

  it('toggleSidebar should toggle sidebarOpen', () => {
    component.toggleSidebar();
    expect(component.sidebarOpen).toBeFalse();
  });
});
