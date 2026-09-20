export interface Availability {
  status?: string;
  target?: string;
  note?: string;
}

export interface ExperienceItem {
  role: string;
  company: string;
  period: string;
  location?: string;
  highlights: string[];
}

export interface EducationItem {
  degree: string;
  institution: string;
  period: string;
}

export interface ProjectItem {
  name: string;
  description: string;
  technologies?: string[];
  role?: string;
  period?: string;
  url?: string;
}

export interface CertificationItem {
  name: string;
  issuer: string;
  year?: string;
  date?: string;
  credential_id?: string;
  url?: string;
}

export interface ResumeData {
  name: string;
  title: string;
  tagline?: string;
  location?: string;
  email?: string;
  phone?: string;
  linkedin?: string;
  github?: string;
  summary: string;
  availability?: Availability;
  experience: ExperienceItem[];
  education: EducationItem[];
  skills: Record<string, string[]>;
  projects?: ProjectItem[];
  certifications?: CertificationItem[];
  publications?: string[];
  document_type?: 'resume' | 'cv';
}

export interface JobInput {
  job_description?: string;
  linkedin_url?: string;
  target_title?: string;
  document_type?: 'resume' | 'cv';
}


export interface LLMConfig {
  provider: 'auto' | 'ollama' | 'openai' | 'huggingface' | 'heuristic';
  model_name?: string;
  api_key?: string;
  base_url?: string;
  temperature: number;
}

export interface AlignmentAuditItem {
  check: string;
  status: 'PASSED' | 'WARNING' | 'FAILED';
  details: string;
}

export interface AlignmentReport {
  match_score: number;
  target_role: string;
  direct_matches: string[];
  transferable_skills: string[];
  unmatched_skills: string[];
  alignment_strategy: string;
  anti_hallucination_audit: AlignmentAuditItem[];
  overall_status: 'PASSED' | 'REJECTED';
}

export interface ThoughtLog {
  step: string;
  content: string;
  timestamp: string;
}

export type GeneratorStep = 'idle' | 'analysis' | 'audit' | 'synthesis' | 'verification' | 'done';

export interface ResumeTemplate {
  id: string;
  name: string;
  description: string;
  is_default: boolean;
}
