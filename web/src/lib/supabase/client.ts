import { createClient as createSupabaseClient } from '@supabase/supabase-js';

// Client-side Supabase client for Client Components
export const createClient = () =>
  createSupabaseClient(
    process.env.NEXT_PUBLIC_SUPABASE_URL!,
    process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!
  );

// Server-side Supabase client for Server Components  
export const createServerClient = () =>
  createSupabaseClient(
    process.env.NEXT_PUBLIC_SUPABASE_URL!,
    process.env.SUPABASE_SERVICE_ROLE_KEY || process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!
  );

// Database types - these should be generated via `supabase gen types typescript`
export interface Database {
  public: {
    Tables: {
      documents: {
        Row: {
          id: string;
          title: string;
          content: string;
          source: string;
          document_type: string;
          metadata: Record<string, unknown>;
          created_at: string;
          updated_at: string;
          processed: boolean;
          embedding?: number[];
          user_id: string;
        };
        Insert: {
          id?: string;
          title: string;
          content: string;
          source: string;
          document_type: string;
          metadata?: Record<string, unknown>;
          processed?: boolean;
          embedding?: number[];
          user_id: string;
        };
        Update: {
          id?: string;
          title?: string;
          content?: string;
          source?: string;
          document_type?: string;
          metadata?: Record<string, unknown>;
          processed?: boolean;
          embedding?: number[];
          user_id?: string;
        };
      };
      entities: {
        Row: {
          id: string;
          name: string;
          entity_type: string;
          confidence: number;
          metadata: Record<string, unknown>;
          document_id: string;
          created_at: string;
          user_id: string;
        };
        Insert: {
          id?: string;
          name: string;
          entity_type: string;
          confidence: number;
          metadata?: Record<string, unknown>;
          document_id: string;
          user_id: string;
        };
        Update: {
          id?: string;
          name?: string;
          entity_type?: string;
          confidence?: number;
          metadata?: Record<string, unknown>;
          document_id?: string;
          user_id?: string;
        };
      };
      analysis_results: {
        Row: {
          id: string;
          document_id: string;
          analysis_type: string;
          result: Record<string, unknown>;
          confidence: number;
          created_at: string;
          user_id: string;
        };
        Insert: {
          id?: string;
          document_id: string;
          analysis_type: string;
          result: Record<string, unknown>;
          confidence: number;
          user_id: string;
        };
        Update: {
          id?: string;
          document_id?: string;
          analysis_type?: string;
          result?: Record<string, unknown>;
          confidence?: number;
          user_id?: string;
        };
      };
    };
    Views: {
      [_ in never]: never;
    };
    Functions: {
      [_ in never]: never;
    };
    Enums: {
      [_ in never]: never;
    };
  };
}

// Type helpers
export type Document = Database['public']['Tables']['documents']['Row'];
export type DocumentInsert = Database['public']['Tables']['documents']['Insert'];
export type DocumentUpdate = Database['public']['Tables']['documents']['Update'];

export type Entity = Database['public']['Tables']['entities']['Row'];
export type EntityInsert = Database['public']['Tables']['entities']['Insert'];
export type EntityUpdate = Database['public']['Tables']['entities']['Update'];

export type AnalysisResult = Database['public']['Tables']['analysis_results']['Row'];
export type AnalysisResultInsert = Database['public']['Tables']['analysis_results']['Insert'];
export type AnalysisResultUpdate = Database['public']['Tables']['analysis_results']['Update'];