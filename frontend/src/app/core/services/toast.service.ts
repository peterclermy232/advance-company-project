import { Injectable } from '@angular/core';
import { MatSnackBar, MatSnackBarConfig } from '@angular/material/snack-bar';

@Injectable({
  providedIn: 'root'
})
export class ToastService {
  constructor(private snackBar: MatSnackBar) {}

  private defaultConfig: MatSnackBarConfig = {
    horizontalPosition: 'right',  
    verticalPosition: 'top',
    duration: 4000  
  };

  success(message: string, duration: number = 4000): void {
    this.snackBar.open(message, undefined, {
      ...this.defaultConfig,
      duration,
      panelClass: ['snackbar-success']
    });
  }

  error(message: string, duration: number = 5000): void {  
    this.snackBar.open(message, undefined, {
      ...this.defaultConfig,
      duration,
      panelClass: ['snackbar-error']
    });
  }

  warning(message: string, duration: number = 4000): void { 
    this.snackBar.open(message, undefined, {
      ...this.defaultConfig,
      duration,
      panelClass: ['snackbar-warning']
    });
  }

  info(message: string, duration: number = 4000): void {  
    this.snackBar.open(message, undefined, {
      ...this.defaultConfig,
      duration,
      panelClass: ['snackbar-info']
    });
  }

  // Custom toast with action button
  withAction(message: string, action: string, duration: number = 4000) { 
    return this.snackBar.open(message, action, {
      ...this.defaultConfig,
      duration
    });
  }

  // Loading toast (stays until dismissed)
  loading(message: string = 'Processing...') {
    return this.snackBar.open(message, '', {
      horizontalPosition: 'right',
      verticalPosition: 'top',
      panelClass: ['snackbar-info']
    });
  }

  // Dismiss all toasts
  dismiss() {
    this.snackBar.dismiss();
  }
}