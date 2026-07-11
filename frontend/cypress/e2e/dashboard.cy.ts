/**
 * Dashboard E2E tests — requires a logged-in user.
 * All API calls are stubbed so tests run without a live backend.
 */
describe('Dashboard', () => {
  const mockUser = {
    id: 1,
    email: 'test@example.com',
    full_name: 'Test User',
    role: 'member',
    email_verified: true,
    activity_status: 'Active',
  };

  beforeEach(() => {
    cy.intercept('GET', '**/accounts/profile/**', {
      body: { success: true, data: mockUser },
    }).as('getProfile');

    cy.intercept('GET', '**/reports/dashboard_summary/**', {
      body: {
        total_members: 42,
        total_contributions: '1500000.00',
        pending_applications: 3,
        active_loans: 5,
      },
    }).as('getDashboardSummary');

    cy.intercept('GET', '**/financial/deposits/monthly_summary/**', {
      body: { results: [] },
    }).as('getMonthlySummary');

    cy.intercept('GET', '**/financial/accounts/**', {
      body: {
        success: true,
        data: {
          total_contributions: '100000.00',
          interest_earned: '5000.00',
          balance: '105000.00',
          loan_limit: '200000.00',
        },
      },
    }).as('getFinancial');

    cy.intercept('GET', '**/notifications/**', {
      body: { success: true, data: [], count: 0, results: [] },
    }).as('getNotifications');

    // Safety net: prevent token-refresh-triggered logout if any unmatched 401 occurs
    cy.intercept('POST', '**/token/refresh/**', {
      body: { access: 'new-fake-access-token' },
    }).as('tokenRefresh');

    // onBeforeLoad is the correct place to seed localStorage — it runs
    // inside the new page's window context before any app code executes
    cy.visit('/dashboard', {
      onBeforeLoad(win) {
        win.localStorage.setItem('access_token', 'fake-access-token');
        win.localStorage.setItem('refresh_token', 'fake-refresh-token');
        win.localStorage.setItem('current_user', JSON.stringify(mockUser));
      },
    });
  });

  it('shows the welcome message with the user name', () => {
    cy.contains('Welcome, Test User').should('be.visible');
  });

  it('shows the user role badge', () => {
    cy.contains('member').should('be.visible');
  });

  it('shows the activity status badge', () => {
    cy.contains('Active').should('be.visible');
  });

  it('has an "Edit Profile" button linking to settings', () => {
    cy.contains('Edit Profile').should('be.visible');
  });

  it('renders the sidebar navigation', () => {
    cy.get('app-sidebar').should('exist');
  });

  it('renders the header', () => {
    cy.get('app-header').should('exist');
  });

  it('shows quick stats section', () => {
    cy.get('app-stat-card').should('have.length.at.least', 1);
  });
});
