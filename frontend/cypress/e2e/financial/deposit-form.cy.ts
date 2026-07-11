/**
 * Deposit Form — member deposit submission.
 * Requires authenticated user. All API calls are stubbed.
 */
describe('Deposit Form', () => {
  const mockUser = {
    id: 1, email: 'member@example.com', full_name: 'Test Member',
    role: 'member', email_verified: true,
  };

  function seedAuth(canDeposit = true) {
    cy.intercept('GET', '**/financial/deposits/can_deposit/**', {
      body: { success: true, message: '', toast_type: 'info',
              data: { can_deposit: canDeposit, message: canDeposit ? '' : 'Already deposited this month.' } },
    }).as('canDeposit');

    cy.intercept('GET', '**/notifications/**', {
      body: { success: true, results: [], count: 0 },
    }).as('getNotifications');

    cy.intercept('POST', '**/token/refresh/**', {
      body: { access: 'new-fake-access-token' },
    }).as('tokenRefresh');

    cy.visit('/deposit-form', {
      onBeforeLoad(win) {
        win.localStorage.setItem('access_token', 'fake-access-token');
        win.localStorage.setItem('refresh_token', 'fake-refresh-token');
        win.localStorage.setItem('current_user', JSON.stringify(mockUser));
      },
    });
  }

  // ── Auth guard ─────────────────────────────────────────────────────────────

  it('redirects to login when not authenticated', () => {
    cy.clearAuthStorage();
    cy.visit('/deposit-form');
    cy.url().should('include', '/auth/login');
  });

  // ── Page load ──────────────────────────────────────────────────────────────

  it('renders the sidebar and header', () => {
    seedAuth();
    cy.get('app-sidebar').should('exist');
    cy.get('app-header').should('exist');
  });

  it('shows the fixed monthly deposit amount', () => {
    seedAuth();
    cy.contains('20,000').should('be.visible');
  });

  it('shows the M-Pesa payment option', () => {
    seedAuth();
    // The "M-Pesa Phone Number" label is visible when mpesa is the selected payment method (default)
    cy.contains('M-Pesa Phone Number').should('be.visible');
  });

  // ── Eligibility check ──────────────────────────────────────────────────────

  it('shows warning when user has already deposited this month', () => {
    seedAuth(false);
    cy.wait('@canDeposit');
    cy.contains(/already deposited/i).should('be.visible');
  });

  // ── M-Pesa form submission ─────────────────────────────────────────────────

  it('submits an M-Pesa deposit and shows confirmation', () => {
    cy.intercept('POST', '**/financial/deposits/**', {
      statusCode: 201,
      body: { success: true, message: 'Deposit initiated.',
              data: { uuid: 'dep-999', mpesa_checkout_request_id: 'ws_CO_123' } },
    }).as('createDeposit');

    seedAuth();
    cy.wait('@canDeposit');

    cy.get('[formControlName="mpesa_phone"]')
      .first()
      .type('0712345678');

    cy.get('button[type="submit"]').click();
    cy.wait('@createDeposit');
    cy.contains(/check your phone|mpesa|stk push/i).should('be.visible');
  });
});
