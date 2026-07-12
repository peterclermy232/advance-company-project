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
