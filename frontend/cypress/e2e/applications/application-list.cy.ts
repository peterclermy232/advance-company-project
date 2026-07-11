/**
 * Application List page.
 * Requires authenticated user. All API calls are stubbed.
 */
describe('Applications List', () => {
  const mockUser = {
    id: 1, email: 'member@example.com', full_name: 'Test Member',
    role: 'member', email_verified: true,
  };

  const mockApplications = [
    {
      id: 'app-001', application_type: 'loan',
      status: 'pending', reason: 'Need emergency funds',
      created_at: '2026-01-10T00:00:00Z',
    },
    {
      id: 'app-002', application_type: 'withdrawal',
      status: 'approved', reason: 'Medical expenses',
      created_at: '2026-01-05T00:00:00Z',
    },
  ];

  beforeEach(() => {
    cy.intercept('GET', '**/applications/**', {
      body: mockApplications,
    }).as('getApplications');

    cy.intercept('GET', '**/notifications/**', {
      body: { success: true, results: [], count: 0 },
    }).as('getNotifications');

    cy.intercept('POST', '**/token/refresh/**', {
      body: { access: 'new-fake-access-token' },
    }).as('tokenRefresh');

    cy.visit('/applications', {
      onBeforeLoad(win) {
        win.localStorage.setItem('access_token', 'fake-access-token');
        win.localStorage.setItem('refresh_token', 'fake-refresh-token');
        win.localStorage.setItem('current_user', JSON.stringify(mockUser));
      },
    });
  });

  // ── Auth guard ─────────────────────────────────────────────────────────────

  it('redirects to login when not authenticated', () => {
    cy.clearAuthStorage();
    cy.visit('/applications');
    cy.url().should('include', '/auth/login');
  });

  // ── Page load ──────────────────────────────────────────────────────────────

  it('shows the Applications heading', () => {
    cy.contains('Applications').should('be.visible');
  });

  it('renders the sidebar and header', () => {
    cy.get('app-sidebar').should('exist');
    cy.get('app-header').should('exist');
  });

  // ── Applications list ──────────────────────────────────────────────────────

  it('renders applications from the API', () => {
    cy.wait('@getApplications');
    cy.contains(/loan|withdrawal/i).should('be.visible');
  });

  it('shows application status badges', () => {
    cy.wait('@getApplications');
    cy.contains('pending').should('be.visible');
    cy.contains('approved').should('be.visible');
  });

  it('shows a button to submit a new application', () => {
    cy.contains(/new application|apply/i).should('be.visible');
  });

  it('navigates to /applications/new when clicking new application button', () => {
    cy.contains(/new application|apply/i).click();
    cy.url().should('include', '/applications/new');
  });

  // ── Empty state ────────────────────────────────────────────────────────────

  it('shows empty state when no applications exist', () => {
    cy.intercept('GET', '**/applications/**', { body: [] }).as('getApplicationsEmpty');

    cy.visit('/applications', {
      onBeforeLoad(win) {
        win.localStorage.setItem('access_token', 'fake-access-token');
        win.localStorage.setItem('refresh_token', 'fake-refresh-token');
        win.localStorage.setItem('current_user', JSON.stringify(mockUser));
      },
    });

    cy.wait('@getApplicationsEmpty');
    cy.contains(/no application|submit your first/i).should('be.visible');
  });
});
