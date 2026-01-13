export interface FinancialAccount {
  id: number;
  user: number;
  user_name?: string;
  total_contributions: number;
  interest_earned: number;
  interest_rate: number;
  created_at: string;
  updated_at: string;
}

export interface Deposit {
  id: number;
  user: number;
  user_name?: string;
  amount: number;
  payment_method: 'mpesa' | 'bank' | 'mansa_x';
  status: 'pending' | 'completed' | 'failed' | 'cancelled';
  transaction_reference: string;
  mpesa_phone?: string;
  notes?: string;
  created_at: string;
  updated_at: string;
}

export interface DepositRequest {
  amount: number;
  payment_method: string;
  mpesa_phone?: string;
  notes?: string;
}

export interface MonthlySummary {
  month: number;
  year: number;
  total_deposits: number;
  count: number;
}

export interface DepositResponse {
  id: number;
  user: number;
  amount: string;
  payment_method: string;
  status: string;
  transaction_reference: string;
  mpesa_phone?: string;
  mpesa_checkout_request_id?: string;
  mpesa_merchant_request_id?: string;
  mpesa_receipt_number?: string;
  created_at: string;
  updated_at: string;
}

export interface CanDepositResponse {
  can_deposit: boolean;
  message: string;
}
