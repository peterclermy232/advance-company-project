/// <reference types="cypress" />

declare global {
  namespace Cypress {
    interface Chainable {
      login(email: string, password: string): Chainable<void>;
      loginViaApi(email?: string, password?: string): Chainable<void>;
      clearAuthStorage(): Chainable<void>;
      interceptLogin(fixture?: string): Chainable<void>;
      interceptRegister(fixture?: string): Chainable<void>;
    }
  }
}

/**
 * Login via UI — fills and submits the login form.
 */
Cypress.Commands.add('login', (email: string, password: string) => {
  cy.visit('/auth/login');
  cy.get('[data-cy="email-input"]').type(email);
  cy.get('[data-cy="password-input"]').type(password);
  cy.get('[data-cy="login-btn"]').click();
});

/**
 * Login via API (bypasses UI) — stores tokens in localStorage directly.
 * Used to quickly set up an authenticated state before non-auth tests.
 */
Cypress.Commands.add('loginViaApi', (
  email = Cypress.env('testUserEmail'),
  password = Cypress.env('testUserPassword'),
) => {
  cy.request({
    method: 'POST',
    url: `${Cypress.env('apiUrl')}/auth/login/`,
    body: { email, password },
    failOnStatusCode: false,
  }).then((response) => {
    if (response.status === 200) {
      const { tokens, user } = response.body.data ?? {};
      if (tokens) {
        window.localStorage.setItem('access_token', tokens.access);
        window.localStorage.setItem('refresh_token', tokens.refresh);
        window.localStorage.setItem('current_user', JSON.stringify(user));
      }
    }
  });
});

/**
 * Clear all auth-related localStorage items.
 */
Cypress.Commands.add('clearAuthStorage', () => {
  cy.window().then((win) => {
    win.localStorage.removeItem('access_token');
    win.localStorage.removeItem('refresh_token');
    win.localStorage.removeItem('current_user');
  });
});

/**
 * Set up a cy.intercept() stub for the login API.
 */
Cypress.Commands.add('interceptLogin', (fixture = 'auth/login-success') => {
  cy.intercept('POST', '**/auth/login/**', { fixture }).as('loginRequest');
});

/**
 * Set up a cy.intercept() stub for the register API.
 */
Cypress.Commands.add('interceptRegister', (fixture = 'auth/register-success') => {
  cy.intercept('POST', '**/auth/register/**', { fixture }).as('registerRequest');
});

export {};
