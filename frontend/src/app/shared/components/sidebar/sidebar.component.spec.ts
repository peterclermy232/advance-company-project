import { ComponentFixture, TestBed } from '@angular/core/testing';
import { provideRouter } from '@angular/router';
import { of } from 'rxjs';
import { SidebarComponent } from './sidebar.component';
import { AuthService } from '../../../core/services/auth.service';

describe('SidebarComponent', () => {
  let fixture: ComponentFixture<SidebarComponent>;
  let component: SidebarComponent;
  let authSpy: jasmine.SpyObj<AuthService>;

  beforeEach(async () => {
    authSpy = jasmine.createSpyObj('AuthService', ['isAdmin', 'logout'], {
      currentUser$: of(null),
    });
    authSpy.isAdmin.and.returnValue(false);

    await TestBed.configureTestingModule({
      imports: [SidebarComponent],
      providers: [
        provideRouter([]),
        { provide: AuthService, useValue: authSpy },
      ],
    }).compileComponents();

    fixture = TestBed.createComponent(SidebarComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });

  it('should default isOpen to true', () => {
    expect(component.isOpen).toBeTrue();
  });

  it('menuItems should not be empty', () => {
    expect(component.menuItems.length).toBeGreaterThan(0);
  });

  it('menuItems should include a dashboard route', () => {
    const dashboard = component.menuItems.find(item => item.id === 'dashboard');
    expect(dashboard).toBeTruthy();
    expect(dashboard!.route).toBe('/dashboard');
  });

  it('isAdmin should delegate to AuthService', () => {
    authSpy.isAdmin.and.returnValue(true);
    expect(component.isAdmin()).toBeTrue();
    authSpy.isAdmin.and.returnValue(false);
    expect(component.isAdmin()).toBeFalse();
  });

  it('logout should call authService.logout', () => {
    component.logout();
    expect(authSpy.logout).toHaveBeenCalled();
  });

  it('adminOnly menu items should exist in the menu', () => {
    const adminItems = component.menuItems.filter(item => item.adminOnly);
    expect(adminItems.length).toBeGreaterThan(0);
  });
});
