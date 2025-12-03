import { createClient } from '@supabase/supabase-js';

const supabaseUrl = process.env.NEXT_PUBLIC_SUPABASE_URL!;
const supabaseAnonKey = process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!;

export const supabase = createClient(supabaseUrl, supabaseAnonKey);

// Database types
export interface Document {
  id: string;
  title: string;
  content: string;
  source: string;
  document_type: string;
  metadata: Record<string, any>;
  created_at: string;
  updated_at: string;
  processed: boolean;
  embedding?: number[];
}

export interface Entity {
  id: string;
  name: string;
  entity_type: string;
  confidence: number;
  metadata: Record<string, any>;
  document_id: string;
  created_at: string;
}

export interface AnalysisResult {
  id: string;
  document_id: string;
  analysis_type: string;
  result: Record<string, any>;
  confidence: number;
  created_at: string;
}