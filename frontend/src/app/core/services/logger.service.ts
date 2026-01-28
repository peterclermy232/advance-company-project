import { Injectable } from '@angular/core';
import { environment } from '../../environments/environment';

@Injectable({
  providedIn: 'root'
})
export class LoggerService {
  private isProduction = environment.production;

  log(...args: any[]): void {
    if (!this.isProduction) {
      console.log(...args);
    }
  }

  error(...args: any[]): void {
    if (!this.isProduction) {
      console.error(...args);
    }
  }

  warn(...args: any[]): void {
    if (!this.isProduction) {
      console.warn(...args);
    }
  }

  info(...args: any[]): void {
    if (!this.isProduction) {
      console.info(...args);
    }
  }

  debug(...args: any[]): void {
    if (!this.isProduction) {
      console.debug(...args);
    }
  }

  table(data: any): void {
    if (!this.isProduction) {
      console.table(data);
    }
  }

  group(label: string): void {
    if (!this.isProduction) {
      console.group(label);
    }
  }

  groupEnd(): void {
    if (!this.isProduction) {
      console.groupEnd();
    }
  }
}