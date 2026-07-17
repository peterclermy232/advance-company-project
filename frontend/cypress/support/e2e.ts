// Import custom commands
import './commands';
import 'cypress-mochawesome-reporter/register';

// Prints browser console output (incl. errors from the app under test) and
// intercepted network activity into the CI terminal log alongside the normal
// Cypress output, instead of only being visible in the video artifact.
require('cypress-terminal-report/src/installLogsCollector')();

// Suppress uncaught exceptions from the app that would fail the test
Cypress.on('uncaught:exception', (err) => {
  // Don't fail tests on Angular zone errors or third-party errors
  if (
    err.message.includes('ResizeObserver') ||
    err.message.includes('zone') ||
    err.message.includes('ExpressionChangedAfterItHasBeenCheckedError')
  ) {
    // Surface it in the command log / video instead of hiding it completely —
    // a suppressed exception thrown mid-handler can abort the rest of that
    // handler silently (e.g. a form submit never reaching its HTTP call),
    // which otherwise shows up only as an unrelated-looking cy.wait() timeout.
    Cypress.log({
      name: 'suppressed exception',
      message: err.message,
      consoleProps: () => ({ error: err, stack: err.stack }),
    });
    return false;
  }
});
