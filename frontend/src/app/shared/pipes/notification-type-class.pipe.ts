import { Pipe, PipeTransform } from '@angular/core';

@Pipe({
  name: 'notificationTypeClass',
  standalone: true
})
export class NotificationTypeClassPipe implements PipeTransform {
  private classes: { [key: string]: string } = {
    'deposit_created': 'bg-blue-100 text-blue-800',
    'deposit_approved': 'bg-green-100 text-green-800',
    'deposit_rejected': 'bg-red-100 text-red-800',
    'application_submitted': 'bg-purple-100 text-purple-800',
    'application_approved': 'bg-green-100 text-green-800',
    'application_rejected': 'bg-red-100 text-red-800',
    'document_verified': 'bg-green-100 text-green-800',
    'document_rejected': 'bg-red-100 text-red-800',
    'beneficiary_verified': 'bg-green-100 text-green-800',
    'system': 'bg-gray-100 text-gray-800',
  };

  transform(type: string): string {
    return this.classes[type] || 'bg-gray-100 text-gray-800';
  }
}
