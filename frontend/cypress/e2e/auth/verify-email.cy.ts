describe('Verify Email Page', () => {
  beforeEach(() => {
    cy.clearAuthStorage();
  });

  // ── No token (direct navigation) ──────────────────────────────────────────

  it('shows error when no email/token query params provided', () => {
    cy.visit('/auth/verify-email');
    cy.contains(/invalid|required/i).should('be.visible');
  });

  // ── Successful verification ────────────────────────────────────────────────

  it('shows success state when verification succeeds', () => {
    cy.intercept('POST', '**/auth/verify-email/**', {
      statusCode: 200,
      body: { success: true, message: 'Email verified successfully.' },
    }).as('verifyEmail');

    cy.visit('/auth/verify-email?email=user@example.com&token=valid-token');

    cy.wait('@verifyEmail');
    cy.contains('Email Verified').should('be.visible');
  });

  it('shows a link to login after successful verification', () => {
    cy.intercept('POST', '**/auth/verify-email/**', {
      statusCode: 200,
      body: { success: true, message: 'Email verified.' },
    }).as('verifyEmail');

    cy.visit('/auth/verify-email?email=user@example.com&token=valid-token');

    cy.wait('@verifyEmail');
    cy.contains('Go to Dashboard').should('be.visible');
  });

  // ── Failed verification ────────────────────────────────────────────────────

  it('shows failure state when token is invalid', () => {
    cy.intercept('POST', '**/auth/verify-email/**', {
      statusCode: 400,
      body: { success: false, message: 'Invalid or expired token.' },
    }).as('verifyEmailFail');

    cy.visit('/auth/verify-email?email=user@example.com&token=bad-token');

    cy.wait('@verifyEmailFail');
    cy.contains('Verification Failed').should('be.visible');
  });

  it('shows resend button on failed verification', () => {
    cy.intercept('POST', '**/auth/verify-email/**', {
      statusCode: 400,
      body: { success: false, message: 'Expired.' },
    }).as('verifyEmailFail');

    cy.visit('/auth/verify-email?email=user@example.com&token=bad-token');

    cy.wait('@verifyEmailFail');
    cy.contains(/resend/i).should('be.visible');
  });
});
