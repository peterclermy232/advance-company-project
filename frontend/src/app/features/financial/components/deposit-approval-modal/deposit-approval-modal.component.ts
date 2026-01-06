import { Component, Input, Output, EventEmitter } from '@angular/core';
import { CommonModule } from '@angular/common';
import { CurrencyFormatPipe } from '../../../../shared/pipes/currency-format.pipe';
import { Deposit } from '../../../../core/models/financial.model';

@Component({
  selector: 'app-deposit-approval-modal',
  standalone: true,
  imports: [CommonModule, CurrencyFormatPipe],
  templateUrl: './deposit-approval-modal.component.html',
})
export class DepositApprovalModalComponent {
  @Input() isOpen = false;
  @Input() deposit: Deposit | null = null;
  @Input() isProcessing = false;

  @Output() confirm = new EventEmitter<void>();
  @Output() cancel = new EventEmitter<void>();

  onConfirm() {
    this.confirm.emit();
  }

  onCancel() {
    this.cancel.emit();
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