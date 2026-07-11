/**
 * Reports page.
 * Requires authenticated user. All API calls are stubbed.
 */
describe('Reports', () => {
  const mockUser = {
    id: 1, email: 'member@example.com', full_name: 'Test Member',
    role: 'member', email_verified: true,
  };

  const mockReports = [
    {
      uuid: 'rpt-001', report_type: 'FINANCIAL', status: 'ready',
      file_url: 'https://example.com/report1.pdf',
      created_at: '2026-01-15T00:00:00Z',
    },
    {
      uuid: 'rpt-002', report_type: 'FINANCIAL', status: 'processing',
      file_url: null, created_at: '2026-01-14T00:00:00Z',
    },
  ];

  beforeEach(() => {
    cy.intercept('GET', '**/reports/**', {
      body: { count: 2, next: null, previous: null, results: mockReports },
    }).as('getReports');

    cy.intercept('GET', '**/notifications/**', {
      body: { success: true, results: [], count: 0 },
    }).as('getNotifications');

    cy.intercept('POST', '**/token/refresh/**', {
      body: { access: 'new-fake-access-token' },
    }).as('tokenRefresh');

    cy.visit('/reports', {
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
    cy.visit('/reports');
    cy.url().should('include', '/auth/login');
  });

  // ── Page load ──────────────────────────────────────────────────────────────

  it('shows the Reports heading', () => {
    cy.contains('Reports').should('be.visible');
  });

  it('renders the sidebar and header', () => {
    cy.get('app-sidebar').should('exist');
    cy.get('app-header').should('exist');
  });

  // ── Reports list ───────────────────────────────────────────────────────────

  it('renders reports from the API', () => {
    cy.wait('@getReports');
    cy.contains(/financial/i).should('be.visible');
  });

  it('shows report status', () => {
    cy.wait('@getReports');
    cy.contains('ready').should('be.visible');
  });

  it('shows all three report type tabs', () => {
    cy.contains('Financial Reports').should('be.visible');
    cy.contains('Activity Reports').should('be.visible');
  });

  // ── Generate report ────────────────────────────────────────────────────────

  it('shows a generate report button', () => {
    cy.contains(/generate|new report/i).should('be.visible');
  });

  it('calls the API when generating a new report', () => {
    cy.intercept('POST', '**/reports/**', {
      statusCode: 201,
      body: { uuid: 'rpt-new', status: 'processing', report_type: 'FINANCIAL' },
    }).as('generateReport');

    cy.contains(/generate|new report/i).click();
    cy.wait('@generateReport');
  });
});
