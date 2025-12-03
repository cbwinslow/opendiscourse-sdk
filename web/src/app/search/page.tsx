import { Metadata } from 'next';
import { Suspense } from 'react';
import { DashboardHeader } from '@/components/dashboard/header';
import { LoadingSpinner } from '@/components/ui/loading-spinner';

export const metadata: Metadata = {
  title: 'Search Documents',
  description: 'Search across government documents with AI-powered semantic search.',
};

export default function SearchPage() {
  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 to-slate-100 dark:from-slate-900 dark:to-slate-800">
      <DashboardHeader />
      
      <main className="container mx-auto px-4 py-8">
        <div className="space-y-6">
          <div className="space-y-2">
            <h1 className="text-3xl font-bold tracking-tight text-slate-900 dark:text-slate-100">
              Document Search
            </h1>
            <p className="text-slate-600 dark:text-slate-400">
              Search across government documents with AI-powered semantic search
            </p>
          </div>

          <Suspense fallback={<LoadingSpinner />}>
            <div className="bg-white dark:bg-slate-800 rounded-lg shadow-sm border p-6">
              <div className="space-y-4">
                <div className="flex flex-col space-y-2">
                  <label htmlFor="search" className="text-sm font-medium text-slate-700 dark:text-slate-300">
                    Search Query
                  </label>
                  <input
                    id="search"
                    type="text"
                    placeholder="Enter your search query..."
                    className="input"
                  />
                </div>
                <button className="btn-primary">
                  Search Documents
                </button>
              </div>
            </div>
          </Suspense>
        </div>
      </main>
    </div>
  );
}