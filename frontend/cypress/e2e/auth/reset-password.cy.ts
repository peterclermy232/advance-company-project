describe('Reset Password Page', () => {
  beforeEach(() => {
    cy.clearAuthStorage();
  });

  // ── Invalid link (no uid/token in query params) ────────────────────────────

  it('shows invalid-link state when no query params are provided', () => {
    cy.visit('/auth/reset-password');
    cy.contains('Invalid Reset Link').should('be.visible');
  });

  it('shows a link back to forgot-password on invalid state', () => {
    cy.visit('/auth/reset-password');
    cy.contains('Request New Link').should('be.visible');
  });

  // ── Valid link (uid + token in query params) ───────────────────────────────

  it('shows the reset-password form when uid and token are provided', () => {
    cy.visit('/auth/reset-password?uid=abc123&token=fake-token');
    cy.contains('Reset Password').should('be.visible');
  });

  it('renders new-password and confirm-password fields', () => {
    cy.visit('/auth/reset-password?uid=abc123&token=fake-token');
    cy.get('[formControlName="new_password"]').should('exist');
    cy.get('[formControlName="confirm_password"]').should('exist');
  });

  // ── Successful reset ───────────────────────────────────────────────────────

  it('redirects to login after successful password reset', () => {
    cy.intercept('POST', '**/auth/reset-password-confirm/**', {
      statusCode: 200,
      body: { success: true, message: 'Password reset successful.' },
    }).as('resetPassword');

    cy.visit('/auth/reset-password?uid=abc123&token=fake-token');

    cy.get('[formControlName="new_password"]').type('NewStr0ng!Pass');
    cy.get('[formControlName="confirm_password"]').type('NewStr0ng!Pass');
    cy.get('button[type="submit"]').click();

    cy.wait('@resetPassword');
    cy.url().should('include', '/auth/login');
  });

  // ── Error state ────────────────────────────────────────────────────────────

  it('shows error message when reset token is expired', () => {
    cy.intercept('POST', '**/auth/reset-password-confirm/**', {
      statusCode: 400,
      body: { success: false, message: 'Reset link has expired.' },
    }).as('resetPasswordFail');

    cy.visit('/auth/reset-password?uid=abc123&token=expired-token');

    cy.get('[formControlName="new_password"]').type('NewStr0ng!Pass');
    cy.get('[formControlName="confirm_password"]').type('NewStr0ng!Pass');
    cy.get('button[type="submit"]').click();

    cy.wait('@resetPasswordFail');
    cy.contains(/expired|invalid|failed/i).should('be.visible');
  });
});
