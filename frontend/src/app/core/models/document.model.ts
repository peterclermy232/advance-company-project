export interface Document {
  id: number;
  user: number;
  user_name?: string;
  category: 'identity' | 'beneficiary' | 'birth_certificate' | 'death_certificate' | 'additional';
  title: string;
  file: string;
  file_url?: string;
  status: 'verified' | 'pending' | 'rejected';
  rejection_reason?: string;
  uploaded_at: string;
  updated_at: string;
}