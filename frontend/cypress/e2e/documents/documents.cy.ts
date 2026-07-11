/**
 * Documents page — Document Centre.
 * Requires authenticated user. All API calls are stubbed.
 */
describe('Document Centre', () => {
  const mockUser = {
    id: 1, email: 'member@example.com', full_name: 'Test Member',
    role: 'member', email_verified: true,
  };

  const mockDocuments = [
    {
      uuid: 'doc-001', title: 'National ID', category: 'identity',
      status: 'approved', file_url: 'https://example.com/id.pdf',
      created_at: '2026-01-01T00:00:00Z',
    },
    {
      uuid: 'doc-002', title: 'Passport Photo', category: 'additional',
      status: 'pending', file_url: 'https://example.com/photo.jpg',
      uploaded_at: '2026-01-02T00:00:00Z',
    },
  ];

  beforeEach(() => {
    cy.intercept('GET', '**/documents/**', {
      body: { count: 2, next: null, previous: null, results: mockDocuments },
    }).as('getDocuments');

    cy.intercept('GET', '**/notifications/**', {
      body: { success: true, results: [], count: 0 },
    }).as('getNotifications');

    cy.intercept('POST', '**/token/refresh/**', {
      body: { access: 'new-fake-access-token' },
    }).as('tokenRefresh');

    cy.visit('/documents', {
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
    cy.visit('/documents');
    cy.url().should('include', '/auth/login');
  });

  // ── Page load ──────────────────────────────────────────────────────────────

  it('shows the Document Centre heading', () => {
    cy.contains('Document Centre').should('be.visible');
  });

  it('renders the sidebar and header', () => {
    cy.get('app-sidebar').should('exist');
    cy.get('app-header').should('exist');
  });

  // ── Document list ──────────────────────────────────────────────────────────

  it('renders document names from the API', () => {
    cy.wait('@getDocuments');
    cy.contains('National ID').should('be.visible');
    cy.contains('Passport Photo').scrollIntoView().should('be.visible');
  });

  it('shows document status badges', () => {
    cy.wait('@getDocuments');
    cy.contains('approved').should('be.visible');
    cy.contains('pending').scrollIntoView().should('be.visible');
  });

  it('shows upload button', () => {
    cy.contains(/upload|add document/i).should('be.visible');
  });

  // ── Empty state ────────────────────────────────────────────────────────────

  it('shows empty state when no documents exist', () => {
    cy.intercept('GET', '**/documents/**', {
      body: { count: 0, next: null, previous: null, results: [] },
    }).as('getDocumentsEmpty');

    cy.visit('/documents', {
      onBeforeLoad(win) {
        win.localStorage.setItem('access_token', 'fake-access-token');
        win.localStorage.setItem('refresh_token', 'fake-refresh-token');
        win.localStorage.setItem('current_user', JSON.stringify(mockUser));
      },
    });

    cy.wait('@getDocumentsEmpty');
    cy.contains(/no document|upload your first/i).should('be.visible');
  });
});
