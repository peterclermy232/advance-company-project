/**
 * Support page — Help & Support.
 * Requires authenticated user. No HTTP calls on load (contact form uses setTimeout simulation).
 */
describe('Support (Help & Support)', () => {
  const mockUser = {
    id: 1, email: 'member@example.com', full_name: 'Test Member',
    role: 'member', email_verified: true,
  };

  beforeEach(() => {
    cy.intercept('GET', '**/notifications/**', {
      body: { success: true, results: [], count: 0 },
    }).as('getNotifications');

    cy.intercept('POST', '**/token/refresh/**', {
      body: { access: 'new-fake-access-token' },
    }).as('tokenRefresh');

    cy.visit('/support', {
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
    cy.visit('/support');
    cy.url().should('include', '/auth/login');
  });

  // ── Page load ──────────────────────────────────────────────────────────────

  it('shows the Help & Support heading', () => {
    cy.contains('Help & Support').should('be.visible');
  });

  it('renders the sidebar and header', () => {
    cy.get('app-sidebar').should('exist');
    cy.get('app-header').should('exist');
  });

  // ── Contact form ───────────────────────────────────────────────────────────

  it('shows a contact form', () => {
    cy.get('form').should('exist');
  });

  it('shows a subject or message input', () => {
    cy.get('input, textarea').should('have.length.at.least', 1);
  });

  it('shows a submit button', () => {
    cy.get('button[type="submit"]').should('exist');
  });

  it('shows success feedback after submitting the contact form', () => {
    cy.get('input[formControlName="subject"]').type('Account question');
    cy.get('textarea[formControlName="message"]')
      .type('I need help with my account.');
    cy.get('button[type="submit"]').click();

    // Component resets the form after 1500ms setTimeout on success
    cy.get('input[formControlName="subject"]', { timeout: 5000 }).should('have.value', '');
    cy.get('textarea[formControlName="message"]').should('have.value', '');
  });

  // ── FAQ / help content ─────────────────────────────────────────────────────

  it('shows FAQ or help content section', () => {
    cy.contains(/faq|frequently asked|help|contact/i).should('be.visible');
  });
});
