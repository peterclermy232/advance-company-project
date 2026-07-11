/**
 * Beneficiary List page.
 * Requires authenticated user. All API calls are stubbed.
 */
describe('Beneficiary List', () => {
  const mockUser = {
    id: 1, email: 'member@example.com', full_name: 'Test Member',
    role: 'member', email_verified: true,
  };

  const mockBeneficiaries = [
    {
      uuid: 'ben-001', name: 'Jane Doe', relation: 'spouse',
      relation_display: 'Spouse', status: 'active',
      verification_status: 'verified', percentage_allocation: 60,
      created_at: '2026-01-01T00:00:00Z',
    },
    {
      uuid: 'ben-002', name: 'John Jr', relation: 'child',
      relation_display: 'Child', status: 'active',
      verification_status: 'pending', percentage_allocation: 40,
      created_at: '2026-01-02T00:00:00Z',
    },
  ];

  beforeEach(() => {
    cy.intercept('GET', '**/beneficiary/**', {
      body: { count: 2, next: null, previous: null, results: mockBeneficiaries },
    }).as('getBeneficiaries');

    cy.intercept('GET', '**/notifications/**', {
      body: { success: true, results: [], count: 0 },
    }).as('getNotifications');

    cy.intercept('POST', '**/token/refresh/**', {
      body: { access: 'new-fake-access-token' },
    }).as('tokenRefresh');

    cy.visit('/beneficiary', {
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
    cy.visit('/beneficiary');
    cy.url().should('include', '/auth/login');
  });

  // ── Page load ──────────────────────────────────────────────────────────────

  it('shows the Beneficiary Management heading', () => {
    cy.contains('Beneficiary Management').should('be.visible');
  });

  it('renders the sidebar and header', () => {
    cy.get('app-sidebar').should('exist');
    cy.get('app-header').should('exist');
  });

  // ── Beneficiary list ───────────────────────────────────────────────────────

  it('renders beneficiaries from the API', () => {
    cy.wait('@getBeneficiaries');
    cy.contains('Jane Doe').should('be.visible');
    cy.contains('John Jr').should('be.visible');
  });

  it('shows percentage allocations', () => {
    cy.wait('@getBeneficiaries');
    cy.contains('60').should('be.visible');
    cy.contains('40').should('be.visible');
  });

  it('shows a button to add a new beneficiary', () => {
    cy.contains(/add beneficiary|new beneficiary/i).should('be.visible');
  });

  it('clicking Add navigates to /beneficiary/add', () => {
    cy.contains(/add beneficiary|new beneficiary/i).click();
    cy.url().should('include', '/beneficiary/add');
  });

  // ── Empty state ────────────────────────────────────────────────────────────

  it('shows empty state when no beneficiaries exist', () => {
    cy.intercept('GET', '**/beneficiary/**', {
      body: { count: 0, next: null, previous: null, results: [] },
    }).as('getBeneficiariesEmpty');

    cy.visit('/beneficiary', {
      onBeforeLoad(win) {
        win.localStorage.setItem('access_token', 'fake-access-token');
        win.localStorage.setItem('refresh_token', 'fake-refresh-token');
        win.localStorage.setItem('current_user', JSON.stringify(mockUser));
      },
    });

    cy.wait('@getBeneficiariesEmpty');
    cy.contains(/no beneficiar/i).should('be.visible');
  });
});
