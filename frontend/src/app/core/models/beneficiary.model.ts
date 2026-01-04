export interface Beneficiary {
  id: number;
  user: number;
  user_name?: string;
  name: string;
  relation: 'spouse' | 'child' | 'parent' | 'sibling' | 'other';
  age: number;
  gender: 'M' | 'F' | 'O';
  phone_number?: string;
  profession?: string;
  salary_range?: string;
  identity_document?: string;
  birth_certificate?: string;
  death_certificate?: string;
  death_certificate_number?: string;
  additional_documents?: string;
  status: 'active' | 'deceased' | 'removed';
  verification_status: 'verified' | 'pending' | 'rejected';
  created_at: string;
  updated_at: string;
}
