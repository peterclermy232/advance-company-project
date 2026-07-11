/**
 * Navigation & route guard tests.
 * These run without a backend — auth state is controlled via localStorage.
 */
describe('Navigation & Route Guards', () => {
  beforeEach(() => {
    cy.clearAuthStorage();
  });

  describe('Unauthenticated redirects', () => {
    it('redirects / to /auth/login', () => {
      cy.visit('/');
      cy.url().should('include', '/auth/login');
    });

    it('redirects /dashboard to /auth/login when not logged in', () => {
      cy.visit('/dashboard');
      cy.url().should('include', '/auth/login');
    });

    it('redirects /financial to /auth/login when not logged in', () => {
      cy.visit('/financial');
      cy.url().should('include', '/auth/login');
    });

    it('redirects /beneficiary to /auth/login when not logged in', () => {
      cy.visit('/beneficiary');
      cy.url().should('include', '/auth/login');
    });

    it('redirects /documents to /auth/login when not logged in', () => {
      cy.visit('/documents');
      cy.url().should('include', '/auth/login');
    });

    it('redirects /reports to /auth/login when not logged in', () => {
      cy.visit('/reports');
      cy.url().should('include', '/auth/login');
    });

    it('redirects /settings to /auth/login when not logged in', () => {
      cy.visit('/settings');
      cy.url().should('include', '/auth/login');
    });

    it('redirects /notifications to /auth/login when not logged in', () => {
      cy.visit('/notifications');
      cy.url().should('include', '/auth/login');
    });

    it('redirects /admin/analytics to /auth/login when not logged in', () => {
      cy.visit('/admin/analytics');
      cy.url().should('include', '/auth/login');
    });

    it('redirects unknown routes to /auth/login', () => {
      cy.visit('/this-route-does-not-exist');
      cy.url().should('include', '/auth/login');
    });
  });

  describe('Public auth routes are always accessible', () => {
    it('/auth/login is accessible without auth', () => {
      cy.visit('/auth/login');
      cy.url().should('include', '/auth/login');
      cy.get('[data-cy="login-form"]').should('exist');
    });

    it('/auth/register is accessible without auth', () => {
      cy.visit('/auth/register');
      cy.url().should('include', '/auth/register');
      cy.get('[data-cy="register-form"]').should('exist');
    });

    it('/auth/forgot-password is accessible without auth', () => {
      cy.visit('/auth/forgot-password');
      cy.url().should('include', '/auth/forgot-password');
      cy.get('[data-cy="forgot-password-form"]').should('exist');
    });
  });
});
