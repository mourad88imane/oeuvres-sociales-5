import type { EmployeeGender, BeneficiaryRelationship } from "@modules/employees/types";

export interface Beneficiary {
  id: string;
  employee: string;
  employee_name: string;
  full_name: string;
  first_name: string;
  last_name: string;
  first_name_ar: string;
  last_name_ar: string;
  gender: EmployeeGender;
  gender_display: string;
  date_of_birth: string;
  age: number | null;
  national_id: string;
  relationship: BeneficiaryRelationship;
  relationship_display: string;
  is_eligible: boolean;
  ineligibility_reason: string;
  is_student: boolean;
  is_handicapped: boolean;
  school_name: string;
  school_year: string;
  spouse_is_employed: boolean | null;
  spouse_employer: string;
  birth_certificate_uploaded: boolean;
  marriage_certificate_uploaded: boolean;
  notes: string;
  created_at: string;
  updated_at: string;
  created_by_name: string;
}

export interface GlobalBeneficiaryResponse {
  status: string;
  count: number;
  data: Beneficiary[];
}
