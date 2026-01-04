export interface Report {
  id: number;
  user: number;
  user_name?: string;
  report_type: 'financial' | 'compensatory' | 'activity';
  title: string;
  file?: string;
  file_url?: string;
  status: 'generating' | 'ready' | 'failed';
  date_from?: string;
  date_to?: string;
  generated_by?: number;
  generated_by_name?: string;
  created_at: string;
  updated_at: string;
}

export interface DashboardSummary {
  total_contributions: number;
  interest_earned: number;
  monthly_deposits: number;
  active_beneficiaries: number;
  total_deposits: number;
}
