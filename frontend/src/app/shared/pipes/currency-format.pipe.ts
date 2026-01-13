import { Pipe, PipeTransform } from '@angular/core';

@Pipe({
  name: 'currencyFormat',
  standalone: true
})
export class CurrencyFormatPipe implements PipeTransform {
  transform(value: number | string | null | undefined, currency: string = 'KES'): string {
    if (value === null || value === undefined) return `${currency} 0.00`;
    
    // Convert string to number if needed
    const numValue = typeof value === 'string' ? parseFloat(value) : value;
    
    // Check if conversion resulted in a valid number
    if (isNaN(numValue)) return `${currency} 0.00`;
    
    return `${currency} ${numValue.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
  }
}