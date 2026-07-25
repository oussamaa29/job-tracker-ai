export type Status =
  | "to_apply"
  | "applied"
  | "phone_screen"
  | "interview"
  | "offer"
  | "rejected"
  | "withdrawn";

export const STATUS_ORDER: Status[] = [
  "to_apply",
  "applied",
  "phone_screen",
  "interview",
  "offer",
  "rejected",
  "withdrawn",
];

export const STATUS_LABELS: Record<Status, string> = {
  to_apply: "À postuler",
  applied: "Postulé",
  phone_screen: "Pré-qualification",
  interview: "Entretien",
  offer: "Offre reçue",
  rejected: "Refusé",
  withdrawn: "Retiré",
};

export interface Application {
  id: number;
  company: string;
  position: string;
  status: Status;
  job_url?: string | null;
  location?: string | null;
  salary_range?: string | null;
  source?: string | null;
  applied_date?: string | null;
  notes?: string | null;
  job_description?: string | null;
  match_score?: number | null;
  match_keywords_matched?: string | null;
  match_keywords_missing?: string | null;
  match_suggestions?: string | null;
  match_reasoning?: string | null;
  created_at: string;
  updated_at: string;
}

export type ApplicationInput = Omit<
  Application,
  | "id"
  | "match_score"
  | "match_keywords_matched"
  | "match_keywords_missing"
  | "match_suggestions"
  | "match_reasoning"
  | "created_at"
  | "updated_at"
>;

export interface Stats {
  total: number;
  by_status: Partial<Record<Status, number>>;
}
