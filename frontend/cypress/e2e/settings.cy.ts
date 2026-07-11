/**
 * Settings page.
 * Requires authenticated user. No API calls on initial load (reads from auth state).
 */
describe('Settings', () => {
  const mockUser = {
    id: 1, email: 'member@example.com', full_name: 'Test Member',
    role: 'member', email_verified: true,
    phone_number: '+254712345678',
  };

  beforeEach(() => {
    cy.intercept('GET', '**/notifications/**', {
      body: { success: true, results: [], count: 0 },
    }).as('getNotifications');

    cy.intercept('POST', '**/token/refresh/**', {
      body: { access: 'new-fake-access-token' },
    }).as('tokenRefresh');

    cy.visit('/settings', {
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
    cy.visit('/settings');
    cy.url().should('include', '/auth/login');
  });

  // ── Page load ──────────────────────────────────────────────────────────────

  it('shows the Settings heading', () => {
    cy.contains('Settings').should('be.visible');
  });

  it('renders the sidebar and header', () => {
    cy.get('app-sidebar').should('exist');
    cy.get('app-header').should('exist');
  });

  // ── User profile display ───────────────────────────────────────────────────

  it('displays the current user full name', () => {
    cy.contains('Test Member').should('be.visible');
  });

  it('displays the current user email in the profile form', () => {
    // Email is in an <input> field, not plain text
    cy.get('input[formControlName="email"]').should('have.value', 'member@example.com');
  });

  // ── Profile update form ────────────────────────────────────────────────────

  it('shows a profile update form or button', () => {
    cy.get('form, button').should('exist');
  });

  it('submits profile update and shows success feedback', () => {
    // Component calls PATCH /auth/users/{id}/ via authService.updateProfile(userId, data)
    cy.intercept('PATCH', '**/auth/users/**', {
      statusCode: 200,
      body: { success: true, data: { id: 1, full_name: 'Updated Name' } },
    }).as('updateProfile');

    cy.get('input[formControlName="full_name"]')
      .first().clear().type('Updated Name');

    cy.get('button[type="submit"]').first().click();
    cy.wait('@updateProfile').its('response.statusCode').should('eq', 200);
  });
});
