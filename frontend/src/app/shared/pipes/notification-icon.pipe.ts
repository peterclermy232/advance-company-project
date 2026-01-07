import { Pipe, PipeTransform } from '@angular/core';

@Pipe({
  name: 'notificationIcon',
  standalone: true
})
export class NotificationIconPipe implements PipeTransform {
  private icons: { [key: string]: string } = {
    'deposit_created': 'M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.402-2.599-1M21 12a9 9 0 11-18 0 9 9 0 0118 0z',
    'deposit_approved': 'M5 13l4 4L19 7',
    'deposit_rejected': 'M6 18L18 6M6 6l12 12',
    'application_submitted': 'M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z',
    'application_approved': 'M5 13l4 4L19 7',
    'application_rejected': 'M6 18L18 6M6 6l12 12',
    'document_verified': 'M5 13l4 4L19 7',
    'document_rejected': 'M6 18L18 6M6 6l12 12',
    'beneficiary_verified': 'M5 13l4 4L19 7',
    'system': 'M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z',
  };

  transform(type: string): string {
    return this.icons[type] || 'M15 17h5l-1.405-1.405A2.032 2.032 0 0118 14.158V11a6.002 6.002 0 00-4-5.659V5a2 2 0 10-4 0v.341C7.67 6.165 6 8.388 6 11v3.159c0 .538-.214 1.055-.595 1.436L4 17h5m6 0v1a3 3 0 11-6 0v-1m6 0H9';
  }
}
