describe('Forgot Password Page', () => {
  beforeEach(() => {
    cy.clearAuthStorage();
    cy.visit('/auth/forgot-password');
  });

  // ── Page loads ─────────────────────────────────────────────────────────────

  it('displays the "Forgot Password?" heading', () => {
    cy.contains('h2', 'Forgot Password?').should('be.visible');
  });

  it('renders the email input and submit button', () => {
    cy.get('[data-cy="email-input"]').should('exist');
    cy.get('[data-cy="send-reset-btn"]').should('exist');
  });

  it('renders a back-to-login link', () => {
    cy.get('[data-cy="back-to-login"]').should('be.visible');
  });

  // ── Validation ─────────────────────────────────────────────────────────────

  it('submit button is disabled when email is empty', () => {
    cy.get('[data-cy="send-reset-btn"]').should('be.disabled');
  });

  it('submit button is disabled for invalid email', () => {
    cy.get('[data-cy="email-input"]').type('invalid-email');
    cy.get('[data-cy="send-reset-btn"]').should('be.disabled');
  });

  it('enables submit button for valid email', () => {
    cy.get('[data-cy="email-input"]').type('valid@example.com');
    cy.get('[data-cy="send-reset-btn"]').should('not.be.disabled');
  });

  // ── Submission ─────────────────────────────────────────────────────────────

  it('shows success state after sending reset link', () => {
    cy.intercept('POST', '**/auth/forgot-password/**', {
      body: {
        success: true,
        message: 'If the email exists, a reset link has been sent.',
      },
    }).as('forgotPassword');

    cy.get('[data-cy="email-input"]').type('user@example.com');
    cy.get('[data-cy="send-reset-btn"]').click();

    cy.wait('@forgotPassword');
    cy.contains('Email Sent').should('be.visible');
  });

  it('shows the submitted email address in the success message', () => {
    cy.intercept('POST', '**/auth/forgot-password/**', {
      body: { success: true, message: 'Sent' },
    }).as('forgotPassword');

    cy.get('[data-cy="email-input"]').type('user@example.com');
    cy.get('[data-cy="send-reset-btn"]').click();

    cy.wait('@forgotPassword');
    cy.contains('user@example.com').should('be.visible');
  });

  it('shows "Send another email" button after success', () => {
    cy.intercept('POST', '**/auth/forgot-password/**', {
      body: { success: true, message: 'Sent' },
    }).as('forgotPassword');

    cy.get('[data-cy="email-input"]').type('user@example.com');
    cy.get('[data-cy="send-reset-btn"]').click();

    cy.wait('@forgotPassword');
    cy.contains('Send another email').should('be.visible');
  });

  it('resets to form when clicking "Send another email"', () => {
    cy.intercept('POST', '**/auth/forgot-password/**', {
      body: { success: true, message: 'Sent' },
    }).as('forgotPassword');

    cy.get('[data-cy="email-input"]').type('user@example.com');
    cy.get('[data-cy="send-reset-btn"]').click();
    cy.wait('@forgotPassword');

    cy.contains('Send another email').click();
    cy.get('[data-cy="forgot-password-form"]').should('be.visible');
  });

  // ── Navigation ─────────────────────────────────────────────────────────────

  it('navigates back to login when clicking the back link', () => {
    cy.get('[data-cy="back-to-login"]').click();
    cy.url().should('include', '/auth/login');
  });
});
