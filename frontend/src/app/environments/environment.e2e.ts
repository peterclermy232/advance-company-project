// Used only by the Angular build's "e2e" configuration (see angular.json).
//
// CI's Cypress jobs serve the app via `ng serve --configuration production`
// but never start a real backend — every network call in the E2E specs is
// stubbed with cy.intercept(). That's fine when apiUrl points at localhost
// (as environment.ts does, which is why `ng serve` with no --configuration
// passes reliably), but environment.prod.ts points at the real deployed
// Render backend. Cypress's request interception has proven unreliable
// against that real, remote, cross-origin HTTPS host specifically — verified
// by reproducing the exact same click/submit flow with Puppeteer, where the
// app fires the request correctly every time, so the app itself isn't at
// fault. This file keeps production's build optimizations (AOT, budgets,
// minification) for E2E fidelity while keeping apiUrl local, matching the
// already-proven-reliable dev-config setup.
export const environment = {
  production: true,
  apiUrl: 'http://127.0.0.1:8000/api',
  apiTimeout: 30000
};
