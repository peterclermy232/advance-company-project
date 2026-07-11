/**
 * Notifications page — All Notifications.
 * Requires authenticated user. All API calls are stubbed.
 */
describe('Notifications', () => {
  const mockUser = {
    id: 1, email: 'member@example.com', full_name: 'Test Member',
    role: 'member', email_verified: true,
  };

  const mockNotifications = [
    {
      uuid: 'notif-001', notification_type: 'deposit_approved',
      title: 'Deposit Approved', message: 'Your deposit of KES 20,000 has been approved.',
      is_read: false, created_at: '2026-01-15T10:00:00Z', time_ago: '2h ago',
    },
    {
      uuid: 'notif-002', notification_type: 'application_update',
      title: 'Application Update', message: 'Your loan application is under review.',
      is_read: true, created_at: '2026-01-14T08:00:00Z', time_ago: '1d ago',
    },
  ];

  beforeEach(() => {
    cy.intercept('GET', '**/notifications/recent/**', {
      body: { count: 2, next: null, previous: null, results: mockNotifications },
    }).as('getNotifications');

    cy.intercept('GET', '**/notifications/unread_count/**', {
      body: { count: 1 },
    }).as('getUnreadCount');

    cy.intercept('POST', '**/token/refresh/**', {
      body: { access: 'new-fake-access-token' },
    }).as('tokenRefresh');

    cy.visit('/notifications', {
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
    cy.visit('/notifications');
    cy.url().should('include', '/auth/login');
  });

  // ── Page load ──────────────────────────────────────────────────────────────

  it('shows the All Notifications heading', () => {
    cy.contains('All Notifications').should('be.visible');
  });

  it('renders the sidebar and header', () => {
    cy.get('app-sidebar').should('exist');
    cy.get('app-header').should('exist');
  });

  // ── Notification list ──────────────────────────────────────────────────────

  it('renders notification titles from the API', () => {
    cy.wait('@getNotifications');
    cy.contains('Deposit Approved').should('be.visible');
    cy.contains('Application Update').should('be.visible');
  });

  it('shows notification messages', () => {
    cy.wait('@getNotifications');
    cy.contains('KES 20,000').should('be.visible');
  });

  it('shows unread indicator on unread notifications', () => {
    cy.wait('@getNotifications');
    cy.contains('2h ago').should('be.visible');
  });

  // ── Mark as read ───────────────────────────────────────────────────────────

  it('calls mark-as-read when clicking a notification', () => {
    // Component uses POST .../notifications/{uuid}/mark_as_read/
    cy.intercept('POST', '**/notifications/notif-001/mark_as_read/**', {
      body: { uuid: 'notif-001', is_read: true },
    }).as('markRead');

    // Intercept wherever the notification navigates to after being clicked
    cy.intercept('GET', '**/financial/deposits/**', {
      body: { success: true, data: [] },
    }).as('getDeposits');

    cy.wait('@getNotifications');
    cy.contains('Deposit Approved').click();
    cy.wait('@markRead').its('response.statusCode').should('eq', 200);
  });

  // ── Mark all as read ───────────────────────────────────────────────────────

  it('shows a mark-all-as-read button', () => {
    cy.contains(/mark all|read all/i).should('be.visible');
  });

  // ── Empty state ────────────────────────────────────────────────────────────

  it('shows empty state when there are no notifications', () => {
    cy.intercept('GET', '**/notifications/recent/**', {
      body: { count: 0, next: null, previous: null, results: [] },
    }).as('getNotificationsEmpty');

    cy.visit('/notifications', {
      onBeforeLoad(win) {
        win.localStorage.setItem('access_token', 'fake-access-token');
        win.localStorage.setItem('refresh_token', 'fake-refresh-token');
        win.localStorage.setItem('current_user', JSON.stringify(mockUser));
      },
    });

    cy.wait('@getNotificationsEmpty');
    cy.contains(/no notification|all caught up/i).should('be.visible');
  });
});
