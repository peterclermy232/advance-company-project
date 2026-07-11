/**
 * Beneficiary Form — add and edit modes.
 * Requires authenticated user. All API calls are stubbed.
 */
describe('Beneficiary Form', () => {
  const mockUser = {
    id: 1, email: 'member@example.com', full_name: 'Test Member',
    role: 'member', email_verified: true,
  };

  function seedAddMode() {
    // Scope to API URL so the intercept does not capture the page navigation to /beneficiary/add
    cy.intercept('GET', '**/api/**/beneficiary/**', {
      body: { count: 0, next: null, previous: null, results: [] },
    }).as('getBeneficiaries');

    cy.intercept('GET', '**/notifications/**', {
      body: { success: true, results: [], count: 0 },
    }).as('getNotifications');

    cy.intercept('POST', '**/token/refresh/**', {
      body: { access: 'new-fake-access-token' },
    }).as('tokenRefresh');

    cy.visit('/beneficiary/add', {
      onBeforeLoad(win) {
        win.localStorage.setItem('access_token', 'fake-access-token');
        win.localStorage.setItem('refresh_token', 'fake-refresh-token');
        win.localStorage.setItem('current_user', JSON.stringify(mockUser));
      },
    });
  }

  // ── Auth guard ─────────────────────────────────────────────────────────────

  it('redirects to login when not authenticated', () => {
    cy.clearAuthStorage();
    cy.visit('/beneficiary/add');
    cy.url().should('include', '/auth/login');
  });

  // ── Add mode ───────────────────────────────────────────────────────────────

  it('renders the sidebar and header in add mode', () => {
    seedAddMode();
    cy.get('app-sidebar').should('exist');
    cy.get('app-header').should('exist');
  });

  it('shows the beneficiary form fields', () => {
    seedAddMode();
    cy.get('input[formControlName="name"], input[name="name"]').should('exist');
  });

  it('shows a percentage_allocation field', () => {
    seedAddMode();
    cy.get('input[formControlName="percentage_allocation"], input[name="percentage_allocation"]')
      .should('exist');
  });

  it('shows validation error when name is too short', () => {
    seedAddMode();
    cy.get('input[formControlName="name"], input[name="name"]').type('AB').blur();
    cy.contains(/min(imum)? 3 characters|too short|at least/i).should('be.visible');
  });

  // ── Successful submission ──────────────────────────────────────────────────

  it('submits form and navigates back to beneficiary list', () => {
    cy.intercept('POST', '**/beneficiary/**', {
      statusCode: 201,
      body: {
        uuid: 'ben-new', name: 'Alice Dep', relation: 'spouse',
        percentage_allocation: 100, status: 'active',
      },
    }).as('createBeneficiary');

    seedAddMode();
    cy.wait('@getBeneficiaries');

    cy.get('input[formControlName="name"]').type('Alice Dep');
    cy.get('select[formControlName="relation"], [formControlName="relation"]')
      .first().select('spouse');
    cy.get('input[formControlName="age"]').type('32');
    cy.get('select[formControlName="gender"], [formControlName="gender"]')
      .first().select('F');
    cy.get('input[formControlName="percentage_allocation"]').clear().type('100');

    // Identity document is required when creating a beneficiary
    cy.get('#identity_document').selectFile({
      contents: Cypress.Buffer.from('fake id contents'),
      fileName: 'id.pdf',
      mimeType: 'application/pdf',
    }, { force: true });

    cy.get('button[type="submit"]').click();
    cy.wait('@createBeneficiary');
    cy.url().should('include', '/beneficiary');
  });
});
