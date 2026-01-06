import { Component, Input, Output, EventEmitter, OnChanges, SimpleChanges } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormBuilder, FormGroup, Validators, ReactiveFormsModule } from '@angular/forms';
import { CurrencyFormatPipe } from '../../../../shared/pipes/currency-format.pipe';
import { Deposit } from '../../../../core/models/financial.model';

@Component({
  selector: 'app-deposit-rejection-modal',
  standalone: true,
  imports: [CommonModule, ReactiveFormsModule, CurrencyFormatPipe],
  templateUrl:'./deposit-rejection-modal.component.html',
})
export class DepositRejectionModalComponent implements OnChanges {
  @Input() isOpen = false;
  @Input() deposit: Deposit | null = null;
  @Input() isProcessing = false;

  @Output() confirm = new EventEmitter<string>();
  @Output() cancel = new EventEmitter<void>();

  rejectForm: FormGroup;

  constructor(private fb: FormBuilder) {
    this.rejectForm = this.fb.group({
      reason: ['', Validators.required]
    });
  }

  ngOnChanges(changes: SimpleChanges) {
    if (changes['isOpen'] && !changes['isOpen'].currentValue) {
      this.rejectForm.reset();
    }
  }

  onSubmit() {
    if (this.rejectForm.valid) {
      const reason = this.rejectForm.get('reason')?.value;
      this.confirm.emit(reason);
    }
  }

  onCancel() {
    this.cancel.emit();
  }
}