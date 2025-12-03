import { createClient as createSupabaseClient } from '@supabase/supabase-js';
import type { Database } from './client';

// Server Component client
export const createServerClient = () =>
  createSupabaseClient<Database>(
    process.env.NEXT_PUBLIC_SUPABASE_URL!,
    process.env.SUPABASE_SERVICE_ROLE_KEY || process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!
  );

// Route Handler client (for API routes)
export const createRouteHandlerSupabaseClient = () =>
  createSupabaseClient<Database>(
    process.env.NEXT_PUBLIC_SUPABASE_URL!,
    process.env.SUPABASE_SERVICE_ROLE_KEY || process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!
  );

// Utility function to get current user in Server Components
export async function getCurrentUser() {
  const supabase = createServerClient();
  const {
    data: { session },
  } = await supabase.auth.getSession();
  
  return session?.user ?? null;
}

// Utility function to require authentication in Server Components
export async function requireAuth() {
  const user = await getCurrentUser();
  
  if (!user) {
    throw new Error('Authentication required');
  }
  
  return user;
}

// Utility function to check if user has specific role
export async function hasRole(role: string) {
  const user = await getCurrentUser();
  
  if (!user) {
    return false;
  }
  
  // Check user metadata for roles
  const userRoles = user.user_metadata?.roles || [];
  return userRoles.includes(role);
}