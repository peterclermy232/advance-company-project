import { bootstrapApplication } from '@angular/platform-browser';
import { appConfig } from './app/app.config';
import { AppComponent } from './app/app.component';
import { environment } from './app/environments/environment';

// ============================================
// DISABLE CONSOLE LOGS IN PRODUCTION
// ============================================
if (environment.production) {
  // Save original console methods (for internal use if needed)
  const originalLog = console.log;
  const originalWarn = console.warn;
  const originalError = console.error;
  const originalInfo = console.info;
  const originalDebug = console.debug;

  // Override console methods to do nothing in production
  console.log = function() {};
  console.warn = function() {};
  console.error = function() {};
  console.info = function() {};
  console.debug = function() {};
  console.table = function() {};
  console.group = function() {};
  console.groupEnd = function() {};
  console.groupCollapsed = function() {};
  console.trace = function() {};
  console.dir = function() {};
  console.dirxml = function() {};
  console.count = function() {};
  console.countReset = function() {};
  console.time = function() {};
  console.timeEnd = function() {};
  console.timeLog = function() {};
  console.assert = function() {};
  console.clear = function() {};

  // Optional: Keep console.error for critical errors only
  // Uncomment if you want to keep error logging in production
  // console.error = originalError;
}

bootstrapApplication(AppComponent, appConfig)
  .catch((err) => {
    // In production, you might want to send this to an error tracking service
    if (!environment.production) {
      console.error(err);
    }
  });