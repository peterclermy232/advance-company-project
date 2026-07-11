import { TestBed, fakeAsync, tick } from '@angular/core/testing';
import {
  HttpTestingController,
  provideHttpClientTesting,
} from '@angular/common/http/testing';
import { provideHttpClient } from '@angular/common/http';
import { provideRouter } from '@angular/router';
import { AuthService } from './auth.service';
import { ToastService } from './toast.service';
import { environment } from '../../environments/environment';

describe('AuthService', () => {
  let service: AuthService;
  let httpMock: HttpTestingController;
  let toastSpy: jasmine.SpyObj<ToastService>;

  const mockUser = {
    id: 1,
    email: 'test@example.com',
    full_name: 'Test User',
    role: 'member',
    email_verified: true,
  };

  const mockAuthResponse = {
    success: true,
    message: 'Login successful',
    toast_type: 'success' as const,
    data: {
      user: mockUser,
      tokens: { access: 'access-token', refresh: 'refresh-token' },
    },
  };

  beforeEach(() => {
    toastSpy = jasmine.createSpyObj('ToastService', [
      'success',
      'error',
      'warning',
      'info',
    ]);

    TestBed.configureTestingModule({
      providers: [
        provideHttpClient(),
        provideHttpClientTesting(),
        provideRouter([]),
        AuthService,
        { provide: ToastService, useValue: toastSpy },
      ],
    });

    service = TestBed.inject(AuthService);
    httpMock = TestBed.inject(HttpTestingController);
    localStorage.clear();
    sessionStorage.clear();
  });

  afterEach(() => {
    httpMock.verify();
    localStorage.clear();
    sessionStorage.clear();
  });

  it('should be created', () => {
    expect(service).toBeTruthy();
  });

  // ── login() ────────────────────────────────────────────────────────────────

  describe('login()', () => {
    it('should POST to the login endpoint', () => {
      const credentials = { email: 'test@example.com', password: 'pass123' };

      service.login(credentials).subscribe();

      const req = httpMock.expectOne(`${environment.apiUrl}/auth/login/`);
      expect(req.request.method).toBe('POST');
      expect(req.request.body).toEqual(credentials);
      req.flush(mockAuthResponse);
    });

    it('should store access_token in localStorage on success', fakeAsync(() => {
      service.login({ email: 'test@example.com', password: 'pass123' }).subscribe();

      const req = httpMock.expectOne(`${environment.apiUrl}/auth/login/`);
      req.flush(mockAuthResponse);
      tick();

      expect(localStorage.getItem('access_token')).toBe('access-token');
    }));

    it('should store refresh_token in localStorage on success', fakeAsync(() => {
      service.login({ email: 'test@example.com', password: 'pass123' }).subscribe();

      const req = httpMock.expectOne(`${environment.apiUrl}/auth/login/`);
      req.flush(mockAuthResponse);
      tick();

      expect(localStorage.getItem('refresh_token')).toBe('refresh-token');
    }));

    it('should emit the user on currentUser$ after login', fakeAsync(() => {
      let emittedUser: any;
      service.currentUser$.subscribe((u) => (emittedUser = u));

      service.login({ email: 'test@example.com', password: 'pass123' }).subscribe();

      const req = httpMock.expectOne(`${environment.apiUrl}/auth/login/`);
      req.flush(mockAuthResponse);
      tick();

      expect(emittedUser?.email).toBe('test@example.com');
    }));

    it('should show a success toast on login', fakeAsync(() => {
      service.login({ email: 'test@example.com', password: 'pass123' }).subscribe();

      const req = httpMock.expectOne(`${environment.apiUrl}/auth/login/`);
      req.flush(mockAuthResponse);
      tick();

      expect(toastSpy.success).toHaveBeenCalledWith('Login successful');
    }));

    it('should show an error toast on 401', fakeAsync(() => {
      service.login({ email: 'test@example.com', password: 'wrong' }).subscribe({
        error: () => {},
      });

      const req = httpMock.expectOne(`${environment.apiUrl}/auth/login/`);
      req.flush(
        { message: 'Invalid credentials', toast_type: 'error', success: false },
        { status: 401, statusText: 'Unauthorized' }
      );
      tick();

      expect(toastSpy.error).toHaveBeenCalled();
    }));
  });

  // ── logout() ───────────────────────────────────────────────────────────────

  describe('logout()', () => {
    it('should remove access_token from localStorage', () => {
      localStorage.setItem('access_token', 'token');
      service.logout();
      expect(localStorage.getItem('access_token')).toBeNull();
    });

    it('should remove refresh_token from localStorage', () => {
      localStorage.setItem('refresh_token', 'refresh');
      service.logout();
      expect(localStorage.getItem('refresh_token')).toBeNull();
    });

    it('should remove current_user from localStorage', () => {
      localStorage.setItem('current_user', JSON.stringify(mockUser));
      service.logout();
      expect(localStorage.getItem('current_user')).toBeNull();
    });

    it('should emit null from currentUser$ after logout', fakeAsync(() => {
      let lastUser: any = 'initial';
      service.currentUser$.subscribe((u) => (lastUser = u));
      service.logout();
      tick();
      expect(lastUser).toBeNull();
    }));
  });

  // ── isAuthenticated() ──────────────────────────────────────────────────────

  describe('isAuthenticated()', () => {
    it('should return false when no token is stored', () => {
      localStorage.removeItem('access_token');
      expect(service.isAuthenticated()).toBeFalse();
    });

    it('should return true when access_token exists', () => {
      localStorage.setItem('access_token', 'some-token');
      expect(service.isAuthenticated()).toBeTrue();
    });
  });

  // ── getToken() ─────────────────────────────────────────────────────────────

  describe('getToken()', () => {
    it('should return stored access token', () => {
      localStorage.setItem('access_token', 'my-token');
      expect(service.getToken()).toBe('my-token');
    });

    it('should return null when no token is stored', () => {
      expect(service.getToken()).toBeNull();
    });
  });

  // ── getCurrentUser() ───────────────────────────────────────────────────────

  describe('getCurrentUser()', () => {
    it('should return null when not logged in', () => {
      expect(service.getCurrentUser()).toBeNull();
    });
  });

  // ── isAdmin() ──────────────────────────────────────────────────────────────

  describe('isAdmin()', () => {
    it('should return false for a regular user', () => {
      expect(service.isAdmin()).toBeFalse();
    });
  });
});
