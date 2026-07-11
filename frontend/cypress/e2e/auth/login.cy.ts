describe('Login Page', () => {
  beforeEach(() => {
    cy.clearAuthStorage();
    // Stub the login API so tests run without a live backend
    cy.intercept('POST', '**/auth/login/**').as('loginRequest');
    cy.visit('/auth/login');
  });

  // ── Page loads ─────────────────────────────────────────────────────────────

  it('redirects to /auth/login from the root URL', () => {
    cy.visit('/');
    cy.url().should('include', '/auth/login');
  });

  it('shows the Advance Company logo', () => {
    cy.contains('Advance').should('be.visible');
    cy.contains('Company').should('be.visible');
  });

  it('displays the "Welcome Back" heading', () => {
    cy.contains('h2', 'Welcome Back').should('be.visible');
  });

  it('renders email input, password input, and submit button', () => {
    cy.get('[data-cy="email-input"]').should('exist');
    cy.get('[data-cy="password-input"]').should('exist');
    cy.get('[data-cy="login-btn"]').should('exist');
  });

  it('has a link to forgot password', () => {
    cy.get('[data-cy="forgot-password-link"]')
      .should('be.visible')
      .and('have.attr', 'href', '/auth/forgot-password');
  });

  it('has a link to the register page', () => {
    cy.get('[data-cy="register-link"]').should('be.visible');
  });

  // ── Form validation ────────────────────────────────────────────────────────

  it('shows validation errors on empty submit', () => {
    cy.get('[data-cy="login-btn"]').click();
    cy.get('[data-cy="email-input"]')
      .should('have.class', 'ng-invalid')
      .and('have.class', 'ng-touched');
  });

  it('rejects invalid email format', () => {
    cy.get('[data-cy="email-input"]').type('not-an-email').blur();
    cy.get('[data-cy="login-btn"]').click();
    cy.get('[data-cy="login-form"]').should('contain', 'valid email');
  });

  it('requires password to be at least 6 characters', () => {
    cy.get('[data-cy="email-input"]').type('test@example.com');
    cy.get('[data-cy="password-input"]').type('abc').blur();
    cy.get('[data-cy="login-btn"]').click();
    cy.get('[data-cy="password-input"]').should('have.class', 'ng-invalid');
  });

  it('disables submit button while loading', () => {
    cy.intercept('POST', '**/auth/login/**', (req) => {
      req.reply({ delay: 2000, fixture: 'auth/login-success' });
    }).as('slowLogin');

    cy.get('[data-cy="email-input"]').type('test@example.com');
    cy.get('[data-cy="password-input"]').type('TestPass123!');
    cy.get('[data-cy="login-btn"]').click();
    cy.get('[data-cy="login-btn"]').should('be.disabled');
    cy.contains('Signing in...').should('be.visible');
  });

  // ── Password toggle ────────────────────────────────────────────────────────

  it('password is hidden by default', () => {
    cy.get('[data-cy="password-input"]').should('have.attr', 'type', 'password');
  });

  it('toggles password visibility on eye-icon click', () => {
    cy.get('[data-cy="password-input"]').type('mypassword');
    cy.get('[data-cy="password-input"]')
      .closest('.relative')
      .find('button[type="button"]')
      .click();
    cy.get('[data-cy="password-input"]').should('have.attr', 'type', 'text');
  });

  // ── Successful login ───────────────────────────────────────────────────────

  it('redirects to /dashboard on successful login', () => {
    cy.intercept('POST', '**/auth/login/**', {
      fixture: 'auth/login-success',
    }).as('loginSuccess');

    cy.get('[data-cy="email-input"]').type('test@example.com');
    cy.get('[data-cy="password-input"]').type('TestPass123!');
    cy.get('[data-cy="login-btn"]').click();

    cy.wait('@loginSuccess');
    cy.url().should('include', '/dashboard');
  });

  it('stores access_token in localStorage after login', () => {
    cy.intercept('POST', '**/auth/login/**', {
      fixture: 'auth/login-success',
    }).as('loginSuccess');

    cy.get('[data-cy="email-input"]').type('test@example.com');
    cy.get('[data-cy="password-input"]').type('TestPass123!');
    cy.get('[data-cy="login-btn"]').click();

    cy.wait('@loginSuccess');
    cy.window().its('localStorage').invoke('getItem', 'access_token').should('not.be.null');
  });

  // ── Failed login ───────────────────────────────────────────────────────────

  it('stays on login page when credentials are wrong', () => {
    cy.intercept('POST', '**/auth/login/**', {
      statusCode: 401,
      fixture: 'auth/login-failure',
    }).as('loginFail');

    cy.get('[data-cy="email-input"]').type('test@example.com');
    cy.get('[data-cy="password-input"]').type('WrongPassword!');
    cy.get('[data-cy="login-btn"]').click();

    cy.wait('@loginFail');
    cy.url().should('include', '/auth/login');
  });

  it('shows error toast on wrong credentials', () => {
    cy.intercept('POST', '**/auth/login/**', {
      statusCode: 401,
      fixture: 'auth/login-failure',
    }).as('loginFail');

    cy.get('[data-cy="email-input"]').type('test@example.com');
    cy.get('[data-cy="password-input"]').type('WrongPassword!');
    cy.get('[data-cy="login-btn"]').click();

    cy.wait('@loginFail');
    // Toast or error message should be visible
    cy.get('body').should('contain.text', 'Invalid');
  });

  // ── 2FA flow ───────────────────────────────────────────────────────────────

  it('shows 2FA modal when backend requires it', () => {
    cy.intercept('POST', '**/auth/login/**', {
      fixture: 'auth/login-2fa',
    }).as('login2FA');

    cy.get('[data-cy="email-input"]').type('2fa@example.com');
    cy.get('[data-cy="password-input"]').type('TestPass123!');
    cy.get('[data-cy="login-btn"]').click();

    cy.wait('@login2FA');
    // The 2FA modal or prompt should appear
    cy.get('body').should('contain.text', 'Two-factor');
  });

  // ── Navigation ─────────────────────────────────────────────────────────────

  it('navigates to forgot-password when clicking the link', () => {
    cy.get('[data-cy="forgot-password-link"]').click();
    cy.url().should('include', '/auth/forgot-password');
  });

  it('navigates to register when clicking "Register here"', () => {
    cy.get('[data-cy="register-link"]').click();
    cy.url().should('include', '/auth/register');
  });
});
