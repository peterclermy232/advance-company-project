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
  user_name: string;
  amount: string;
  payment_method: 'mpesa' | 'bank' | 'mansa_x';
  status: 'pending' | 'completed' | 'processing' | 'failed' | 'cancelled';
  transaction_reference: string;
  mpesa_phone: string | null;
  notes: string | null;
  mpesa_checkout_request_id: string | null;
  mpesa_merchant_request_id: string | null;
  mpesa_receipt_number: string | null;
  mpesa_transaction_date: string | null;
  mpesa_response_code: string | null;
  mpesa_response_description: string | null;
  approved_at: string | null;
  rejected_at: string | null;
  rejection_reason: string | null; // Added this missing property
  created_at: string;
  updated_at: string;
  user: number;
  approved_by: number | null;
  rejected_by: number | null;
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

export interface DepositSummary {
  total: number;
  pending: number;
  approved: number;
  rejected: number;
  processing: number;
}