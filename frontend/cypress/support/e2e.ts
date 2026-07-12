// Import custom commands
import './commands';
import 'cypress-mochawesome-reporter/register';

// Suppress uncaught exceptions from the app that would fail the test
Cypress.on('uncaught:exception', (err) => {
  // Don't fail tests on Angular zone errors or third-party errors
  if (
    err.message.includes('ResizeObserver') ||
    err.message.includes('zone') ||
    err.message.includes('ExpressionChangedAfterItHasBeenCheckedError')
  ) {
    return false;
  }
});
