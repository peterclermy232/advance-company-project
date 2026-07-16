import { defineConfig } from "cypress";

export default defineConfig({
  projectId: "y5ekxq",

  reporter: "cypress-multi-reporters",
  reporterOptions: {
    configFile: "reporter-config.json",
  },

  e2e: {
    baseUrl: "http://localhost:4200",
    specPattern: "cypress/e2e/**/*.cy.ts",
    supportFile: "cypress/support/e2e.ts",
    fixturesFolder: "cypress/fixtures",
    screenshotsFolder: "cypress/screenshots",
    videosFolder: "cypress/videos",
    video: false,
    screenshotOnRunFailure: true,
    defaultCommandTimeout: 8000,
    requestTimeout: 10000,

    setupNodeEvents(on, config) {
      require("cypress-mochawesome-reporter/plugin")(on);

      // Chrome's back/forward cache (bfcache) can serve a page from a
      // frozen, paused JS snapshot instead of a genuine reload when
      // cy.visit() repeatedly navigates to the same URL within one spec
      // (e.g. every login.cy.ts test visiting '/auth/login' in beforeEach).
      // That resumed snapshot can carry over stale RxJS/Zone.js state from
      // the previous test's in-flight request, which perpetually hangs the
      // new test's own request (observed as a stuck "Signing in..." spinner
      // and Cypress never seeing a matching request). Disabling bfcache
      // forces a genuine fresh load every time.
      on("before:browser:launch", (browser, launchOptions) => {
        if (browser.family === "chromium" && browser.name !== "electron") {
          launchOptions.args.push("--disable-features=BackForwardCache");
        }
        return launchOptions;
      });

      return config;
    },

    env: {
      apiUrl: "http://127.0.0.1:8000/api/v1",
      testUserEmail: "test@example.com",
      testUserPassword: "TestPass123!",
    },
  },

  component: {
    devServer: {
      framework: "angular",
      bundler: "webpack",
    },
    specPattern: "**/*.cy.ts",
  },
});
