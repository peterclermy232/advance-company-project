interface MemberAnalytics {
  id: number;
  full_name: string;
  email: string;
  phone_number: string;
  total_contributions: number;
  total_deposits: number;
  interest_earned: number;
  activity_status: string;
  created_at: string;
  last_deposit_date?: string;
  contribution_percentage: number;
}

interface AnalyticsSummary {
  total_contributions: number;
  total_members: number;
  active_members: number;
  average_contribution: number;
  total_deposits_count: number;
  total_interest_earned: number;
  monthly_growth_rate: number;
}

interface MonthlyTrend {
  month: string;
  year: number;
  total_amount: number;
  deposit_count: number;
  member_count: number;
}
export { MemberAnalytics, AnalyticsSummary, MonthlyTrend };