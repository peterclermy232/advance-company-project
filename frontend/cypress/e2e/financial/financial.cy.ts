/**
 * Financial page — admin deposit approval view.
 * Requires authenticated user. All API calls are stubbed.
 */
describe('Financial (Deposit Approvals)', () => {
  const mockUser = {
    id: 1, email: 'admin@example.com', full_name: 'Admin User',
    role: 'admin', email_verified: true,
  };

  const mockDeposits = [
    {
      uuid: 'dep-001', amount: '20000.00', status: 'pending',
      user_name: 'Alice Member', payment_method: 'mpesa',
      created_at: '2026-01-15T10:00:00Z',
    },
    {
      uuid: 'dep-002', amount: '20000.00', status: 'completed',
      user_name: 'Bob Member', payment_method: 'bank_transfer',
      created_at: '2026-01-14T09:00:00Z',
    },
  ];

  beforeEach(() => {
    cy.intercept('GET', '**/financial/deposits/**', {
      body: { success: true, message: '', toast_type: 'info', data: mockDeposits },
    }).as('getDeposits');

    cy.intercept('GET', '**/notifications/**', {
      body: { success: true, results: [], count: 0 },
    }).as('getNotifications');

    cy.intercept('POST', '**/token/refresh/**', {
      body: { access: 'new-fake-access-token' },
    }).as('tokenRefresh');

    cy.visit('/financial', {
      onBeforeLoad(win) {
        win.localStorage.setItem('access_token', 'fake-access-token');
        win.localStorage.setItem('refresh_token', 'fake-refresh-token');
        win.localStorage.setItem('current_user', JSON.stringify(mockUser));
      },
    });
  });

  // ── Page load ──────────────────────────────────────────────────────────────

  it('shows the Deposit Approvals heading', () => {
    cy.contains('Deposit Approvals').should('be.visible');
  });

  it('renders the sidebar', () => {
    cy.get('app-sidebar').should('exist');
  });

  it('renders the header', () => {
    cy.get('app-header').should('exist');
  });

  // ── Auth guard ─────────────────────────────────────────────────────────────

  it('redirects to login when not authenticated', () => {
    cy.clearAuthStorage();
    cy.visit('/financial');
    cy.url().should('include', '/auth/login');
  });

  // ── Deposit list ───────────────────────────────────────────────────────────

  it('renders deposit rows from API response', () => {
    cy.wait('@getDeposits');
    // Default filter is "Pending" — Alice (pending) is visible in this tab
    cy.contains('Alice Member').should('be.visible');
  });

  it('shows completed deposits on the Approved tab', () => {
    cy.wait('@getDeposits');
    cy.contains('Approved').click();
    cy.contains('Bob Member').should('be.visible');
  });

  it('shows deposit amounts', () => {
    cy.wait('@getDeposits');
    cy.contains('20,000').should('be.visible');
  });
});
