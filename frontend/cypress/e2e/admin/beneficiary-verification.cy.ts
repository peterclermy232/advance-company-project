/**
 * Beneficiary Verification page — admin only.
 * Requires admin user. All API calls are stubbed.
 */
describe('Beneficiary Verification', () => {
  const adminUser = {
    id: 2, email: 'admin@example.com', full_name: 'Admin User',
    role: 'admin', email_verified: true,
  };

  const mockStats = { total: 5, pending: 2, verified: 2, rejected: 1 };

  const mockPendingBeneficiaries = [
    {
      uuid: 'ben-001', user_name: 'John Member', user_email: 'john@example.com',
      user_phone: '0712345678', name: 'Jane Dep', relation: 'spouse',
      relation_display: 'Spouse', age: 30, gender: 'F',
      verification_status: 'pending', verification_status_display: 'Pending Review',
      status: 'active', identity_document_url: 'https://example.com/id.pdf',
      created_at: '2026-01-10T00:00:00Z',
    },
  ];

  beforeEach(() => {
    // Register the list intercept FIRST so the more-specific statistics
    // intercept (registered last) takes priority when both match.
    cy.intercept('GET', '**/beneficiary/**', {
      body: { count: 1, next: null, previous: null, results: mockPendingBeneficiaries },
    }).as('getBeneficiaries');

    cy.intercept('GET', '**/beneficiary/statistics/**', {
      body: mockStats,
    }).as('getStats');

    cy.intercept('GET', '**/notifications/**', {
      body: { success: true, results: [], count: 0 },
    }).as('getNotifications');

    cy.intercept('POST', '**/token/refresh/**', {
      body: { access: 'new-fake-access-token' },
    }).as('tokenRefresh');

    cy.visit('/admin/beneficiary-verification', {
      onBeforeLoad(win) {
        win.localStorage.setItem('access_token', 'fake-access-token');
        win.localStorage.setItem('refresh_token', 'fake-refresh-token');
        win.localStorage.setItem('current_user', JSON.stringify(adminUser));
      },
    });
  });

  // ── Auth / role guard ──────────────────────────────────────────────────────

  it('redirects to login when not authenticated', () => {
    cy.clearAuthStorage();
    cy.visit('/admin/beneficiary-verification');
    cy.url().should('include', '/auth/login');
  });

  // ── Page load ──────────────────────────────────────────────────────────────

  it('shows the Beneficiary Verification heading', () => {
    cy.contains('Beneficiary Verification').should('be.visible');
  });

  it('renders the sidebar and header', () => {
    cy.get('app-sidebar').should('exist');
    cy.get('app-header').should('exist');
  });

  // ── Stats ──────────────────────────────────────────────────────────────────

  it('shows total beneficiary count from stats API', () => {
    cy.wait('@getStats');
    cy.contains('5').should('be.visible');
  });

  it('shows pending count from stats API', () => {
    cy.wait('@getStats');
    cy.contains('2').should('be.visible');
  });

  // ── Pending list ───────────────────────────────────────────────────────────

  it('renders pending beneficiaries', () => {
    cy.wait('@getBeneficiaries');
    cy.contains('John Member').should('be.visible');
    cy.contains('Jane Dep').should('be.visible');
  });

  it('shows Pending Review status', () => {
    cy.wait('@getBeneficiaries');
    cy.contains('Pending Review').should('be.visible');
  });

  // ── Verify action ──────────────────────────────────────────────────────────

  it('shows Verify button for pending beneficiary', () => {
    cy.wait('@getBeneficiaries');
    cy.contains('button', 'Verify').should('be.visible');
  });

  it('calls verify API when clicking Verify button', () => {
    cy.intercept('POST', '**/beneficiary/ben-001/verify/**', {
      body: { uuid: 'ben-001', verification_status: 'verified' },
    }).as('verifyBeneficiary');

    cy.window().then((win) => cy.stub(win, 'confirm').returns(true));

    cy.wait('@getBeneficiaries');
    cy.contains('button', 'Verify').first().click();
    cy.wait('@verifyBeneficiary');
  });

  // ── Reject action ──────────────────────────────────────────────────────────

  it('shows Reject button for pending beneficiary', () => {
    cy.wait('@getBeneficiaries');
    cy.contains('Reject').should('be.visible');
  });

  // ── Empty state ────────────────────────────────────────────────────────────

  it('shows empty state when no pending beneficiaries', () => {
    cy.intercept('GET', '**/beneficiary/**', {
      body: { count: 0, next: null, previous: null, results: [] },
    }).as('getBeneficiariesEmpty');

    cy.visit('/admin/beneficiary-verification', {
      onBeforeLoad(win) {
        win.localStorage.setItem('access_token', 'fake-access-token');
        win.localStorage.setItem('refresh_token', 'fake-refresh-token');
        win.localStorage.setItem('current_user', JSON.stringify(adminUser));
      },
    });

    cy.wait('@getBeneficiariesEmpty');
    cy.contains('No beneficiaries found').should('be.visible');
  });
});
