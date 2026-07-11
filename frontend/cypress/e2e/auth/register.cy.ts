describe('Register Page', () => {
  beforeEach(() => {
    cy.clearAuthStorage();
    cy.visit('/auth/register');
  });

  // ── Page loads ─────────────────────────────────────────────────────────────

  it('displays the "Create Account" heading', () => {
    cy.contains('h2', 'Create Account').should('be.visible');
  });

  it('renders all required form fields', () => {
    cy.get('[data-cy="full-name-input"]').should('exist');
    cy.get('[data-cy="email-input"]').should('exist');
    cy.get('[data-cy="phone-input"]').should('exist');
    cy.get('[data-cy="password-input"]').should('exist');
    cy.get('[data-cy="confirm-password-input"]').should('exist');
    cy.get('[data-cy="register-btn"]').should('exist');
  });

  it('has a link back to login', () => {
    cy.contains('Sign in here').should('be.visible');
  });

  // ── Form validation ────────────────────────────────────────────────────────

  it('submit button is disabled when form is invalid', () => {
    cy.get('[data-cy="register-btn"]').should('be.disabled');
  });

  it('shows password requirements checklist', () => {
    cy.contains('Password must contain').should('be.visible');
    cy.contains('One uppercase letter').should('be.visible');
    cy.contains('One number').should('be.visible');
    cy.contains('At least 12 characters').should('be.visible');
  });

  it('password requirements turn green when met', () => {
    cy.get('[data-cy="password-input"]').type('Str0ngP@ssword!');
    cy.contains('One uppercase letter').should('have.class', 'text-green-600');
    cy.contains('One number').should('have.class', 'text-green-600');
    cy.contains('At least 12 characters').should('have.class', 'text-green-600');
  });

  it('shows error when passwords do not match', () => {
    cy.get('[data-cy="password-input"]').type('Str0ngP@ssword!');
    cy.get('[data-cy="confirm-password-input"]').type('DifferentPass1!').blur();
    cy.get('[data-cy="register-form"]').should('contain.text', 'match');
  });

  it('rejects invalid email format', () => {
    cy.get('[data-cy="email-input"]').type('not-valid').blur();
    cy.get('[data-cy="email-input"]').should('have.class', 'ng-invalid');
  });

  it('rejects short phone number', () => {
    cy.get('[data-cy="phone-input"]').type('123').blur();
    cy.get('[data-cy="phone-input"]').should('have.class', 'ng-invalid');
  });

  // ── Successful registration ────────────────────────────────────────────────

  it('submits and redirects to verify-email on success', () => {
    cy.intercept('POST', '**/auth/register/**', {
      fixture: 'auth/register-success',
    }).as('registerSuccess');

    cy.get('[data-cy="full-name-input"]').type('New User');
    cy.get('[data-cy="email-input"]').type('newuser@example.com');
    cy.get('[data-cy="phone-input"]').type('+254712345678');
    cy.get('[data-cy="password-input"]').type('Str0ngP@ssword!');
    cy.get('[data-cy="confirm-password-input"]').type('Str0ngP@ssword!');
    cy.get('[data-cy="register-btn"]').click();

    cy.wait('@registerSuccess');
    cy.url().should('include', '/auth/verify-email');
  });

  it('shows loading state while submitting', () => {
    cy.intercept('POST', '**/auth/register/**', (req) => {
      req.reply({ delay: 2000, fixture: 'auth/register-success' });
    }).as('slowRegister');

    cy.get('[data-cy="full-name-input"]').type('Slow User');
    cy.get('[data-cy="email-input"]').type('slow@example.com');
    cy.get('[data-cy="phone-input"]').type('+254712345678');
    cy.get('[data-cy="password-input"]').type('Str0ngP@ssword!');
    cy.get('[data-cy="confirm-password-input"]').type('Str0ngP@ssword!');
    cy.get('[data-cy="register-btn"]').click();

    cy.contains('Creating account...').should('be.visible');
    cy.get('[data-cy="register-btn"]').should('be.disabled');
  });

  // ── Navigation ─────────────────────────────────────────────────────────────

  it('navigates to login when clicking "Sign in here"', () => {
    cy.contains('Sign in here').click();
    cy.url().should('include', '/auth/login');
  });
});
