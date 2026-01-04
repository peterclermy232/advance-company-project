export interface Application {
  id: number;
  user: number;
  user_name?: string;
  application_type: 'entry' | 'exit';
  reason: string;
  supporting_document?: string;
  status: 'pending' | 'under_review' | 'approved' | 'rejected';
  admin_comments?: string;
  submitted_at: string;
  reviewed_at?: string;
  approved_at?: string;
  reviewed_by?: number;
  created_at: string;
  updated_at: string;
  activities?: ApplicationActivity[];
}

export interface ApplicationActivity {
  id: number;
  application: number;
  user: number;
  user_name?: string;
  action: string;
  notes?: string;
  created_at: string;
}
