import { Injectable } from '@angular/core';
import { MatSnackBar, MatSnackBarConfig, MatSnackBarRef, TextOnlySnackBar } from '@angular/material/snack-bar';

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

  success(message: string, duration = 4000): void {
    this.snackBar.open(message, undefined, {
      ...this.defaultConfig,
      duration,
      panelClass: ['snackbar-success']
    });
  }

  error(message: string, duration = 5000): void {
    this.snackBar.open(message, undefined, {
      ...this.defaultConfig,
      duration,
      panelClass: ['snackbar-error']
    });
  }

  warning(message: string, duration = 4000): void {
    this.snackBar.open(message, undefined, {
      ...this.defaultConfig,
      duration,
      panelClass: ['snackbar-warning']
    });
  }

  info(message: string, duration = 4000): void {
    this.snackBar.open(message, undefined, {
      ...this.defaultConfig,
      duration,
      panelClass: ['snackbar-info']
    });
  }

  withAction(message: string, action: string, duration = 6000): MatSnackBarRef<TextOnlySnackBar> {
    return this.snackBar.open(message, action, {
      ...this.defaultConfig,
      duration
    });
  }

  loading(message = 'Processing...'): MatSnackBarRef<TextOnlySnackBar> {
    return this.snackBar.open(message, '', {
      horizontalPosition: 'right',
      verticalPosition: 'top',
      panelClass: ['snackbar-info']
      // no duration — caller must call .dismiss()
    });
  }

  dismiss(): void {
    this.snackBar.dismiss();
  }
}