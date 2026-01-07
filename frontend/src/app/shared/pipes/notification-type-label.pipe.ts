import { Pipe, PipeTransform } from '@angular/core';

@Pipe({
  name: 'notificationTypeLabel',
  standalone: true
})
export class NotificationTypeLabelPipe implements PipeTransform {
  private labels: { [key: string]: string } = {
    'deposit_created': 'Deposit',
    'deposit_approved': 'Approved',
    'deposit_rejected': 'Rejected',
    'application_submitted': 'Application',
    'application_approved': 'Approved',
    'application_rejected': 'Rejected',
    'document_verified': 'Verified',
    'document_rejected': 'Rejected',
    'beneficiary_verified': 'Verified',
    'system': 'System',
  };

  transform(type: string): string {
    return this.labels[type] || 'Notification';
  }
}
