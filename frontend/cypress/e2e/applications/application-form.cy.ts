/**
 * Application Form — new application submission.
 * Requires authenticated user. All API calls are stubbed.
 */
describe('Application Form', () => {
  const mockUser = {
    id: 1, email: 'member@example.com', full_name: 'Test Member',
    role: 'member', email_verified: true,
  };

  const mockChoices = {
    application_types: [
      { value: 'loan', label: 'Loan Application', description: 'Apply for a loan' },
      { value: 'withdrawal', label: 'Withdrawal', description: 'Withdraw contributions' },
    ],
    status_choices: [
      { value: 'pending', label: 'Pending' },
    ],
  };

  beforeEach(() => {
    cy.intercept('GET', '**/applications/choices/**', {
      body: mockChoices,
    }).as('getChoices');

    cy.intercept('GET', '**/notifications/**', {
      body: { success: true, results: [], count: 0 },
    }).as('getNotifications');

    cy.intercept('POST', '**/token/refresh/**', {
      body: { access: 'new-fake-access-token' },
    }).as('tokenRefresh');

    cy.visit('/applications/new', {
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
    cy.visit('/applications/new');
    cy.url().should('include', '/auth/login');
  });

  // ── Page load ──────────────────────────────────────────────────────────────

  it('renders the sidebar and header', () => {
    cy.get('app-sidebar').should('exist');
    cy.get('app-header').should('exist');
  });

  it('shows the application form', () => {
    cy.wait('@getChoices');
    cy.get('form').should('exist');
  });

  it('shows application type options from the API', () => {
    cy.wait('@getChoices');
    // <option> elements are 0×0 pixels in browsers — check the <select> has options instead
    cy.get('select[formControlName="application_type"]')
      .find('option').should('have.length.at.least', 2);
  });

  // ── Validation ─────────────────────────────────────────────────────────────

  it('submit button is disabled when form is empty', () => {
    cy.wait('@getChoices');
    cy.get('button[type="submit"]').should('be.disabled');
  });

  // ── Successful submission ──────────────────────────────────────────────────

  it('submits application and navigates back to applications list', () => {
    cy.intercept('POST', '**/applications/**', {
      statusCode: 201,
      body: { id: 'app-new', application_type: 'loan', status: 'pending' },
    }).as('createApplication');

    cy.wait('@getChoices');

    cy.get('select[formControlName="application_type"], [formControlName="application_type"]')
      .first().select('loan');
    cy.get('textarea[formControlName="reason"], [formControlName="reason"]')
      .first().type('I need funds for medical expenses.');
    cy.get('button[type="submit"]').click();

    cy.wait('@createApplication');
    cy.url().should('include', '/applications');
  });
});
