/**
 * Admin Analytics Dashboard — admin only.
 * Requires admin user. All API calls are stubbed.
 */
describe('Admin Analytics Dashboard', () => {
  const adminUser = {
    id: 2, email: 'admin@example.com', full_name: 'Admin User',
    role: 'admin', email_verified: true,
  };

  const mockAnalytics = {
    members: [
      {
        full_name: 'Alice Member', email: 'alice@example.com',
        total_contributions: 60000, total_deposits: 3, interest_earned: 1500,
      },
      {
        full_name: 'Bob Member', email: 'bob@example.com',
        total_contributions: 40000, total_deposits: 2, interest_earned: 1000,
      },
    ],
    summary: {
      total_members: 2, total_contributions: 100000, average_contributions: 50000,
    },
    monthly_trends: [
      { month: 'January', year: 2026, total_amount: 60000, deposit_count: 3 },
      { month: 'February', year: 2026, total_amount: 40000, deposit_count: 2 },
    ],
  };

  beforeEach(() => {
    cy.intercept('GET', '**/admin/analytics/members/**', {
      body: mockAnalytics,
    }).as('getMemberAnalytics');

    cy.intercept('GET', '**/notifications/**', {
      body: { success: true, results: [], count: 0 },
    }).as('getNotifications');

    cy.intercept('POST', '**/token/refresh/**', {
      body: { access: 'new-fake-access-token' },
    }).as('tokenRefresh');

    cy.visit('/admin/analytics', {
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
    cy.visit('/admin/analytics');
    cy.url().should('include', '/auth/login');
  });

  // ── Page load ──────────────────────────────────────────────────────────────

  it('shows the Admin Analytics Dashboard heading', () => {
    cy.contains('Admin Analytics Dashboard').should('be.visible');
  });

  it('renders the sidebar and header', () => {
    cy.get('app-sidebar').should('exist');
    cy.get('app-header').should('exist');
  });

  // ── Analytics data ─────────────────────────────────────────────────────────

  it('shows member names from the API', () => {
    cy.wait('@getMemberAnalytics');
    cy.contains('Alice Member').should('be.visible');
    cy.contains('Bob Member').should('be.visible');
  });

  it('shows total members count', () => {
    cy.wait('@getMemberAnalytics');
    cy.contains('2').should('be.visible');
  });

  it('shows contribution data', () => {
    cy.wait('@getMemberAnalytics');
    cy.contains(/100,000|100000/i).should('be.visible');
  });

  // ── Export ─────────────────────────────────────────────────────────────────

  it('shows export buttons', () => {
    cy.wait('@getMemberAnalytics');
    cy.contains(/export/i).scrollIntoView().should('be.visible');
  });
});
