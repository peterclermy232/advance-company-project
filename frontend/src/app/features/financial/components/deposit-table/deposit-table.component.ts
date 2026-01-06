import { Component, Input, Output, EventEmitter } from '@angular/core';
import { CommonModule } from '@angular/common';
import { CurrencyFormatPipe } from '../../../../shared/pipes/currency-format.pipe';
import { Deposit } from '../../../../core/models/financial.model';

@Component({
  selector: 'app-deposit-table',
  standalone: true,
  imports: [CommonModule, CurrencyFormatPipe],
  templateUrl: './deposit-table.component.html'
})
export class DepositTableComponent {
  @Input() deposits: Deposit[] = [];
  @Input() filterStatus: 'pending' | 'completed' | 'failed' = 'pending';
  @Input() pendingCount = 0;
  @Input() approvedCount = 0;
  @Input() rejectedCount = 0;

  @Output() approve = new EventEmitter<Deposit>();
  @Output() reject = new EventEmitter<Deposit>();
  @Output() filterChange = new EventEmitter<'pending' | 'completed' | 'failed'>();

  onApprove(deposit: Deposit) {
    this.approve.emit(deposit);
  }

  onReject(deposit: Deposit) {
    this.reject.emit(deposit);
  }

  onFilterChange(status: 'pending' | 'completed' | 'failed') {
    this.filterChange.emit(status);
  }

  getStatusClass(status: string): string {
    const classes: { [key: string]: string } = {
      'completed': 'bg-green-100 text-green-800',
      'pending': 'bg-yellow-100 text-yellow-800',
      'failed': 'bg-red-100 text-red-800',
      'cancelled': 'bg-gray-100 text-gray-800'
    };
    return classes[status] || 'bg-gray-100 text-gray-800';
  }

  getPaymentMethodLabel(method: string): string {
    const labels: { [key: string]: string } = {
      'mpesa': 'M-Pesa',
      'bank': 'Bank Transfer',
      'mansa_x': 'Mansa-X'
    };
    return labels[method] || method;
  }
}