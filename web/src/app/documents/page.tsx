'use client';

import { DashboardHeader } from '@/components/dashboard/header';
import { AdvancedDocumentAnalysis } from '@/components/analysis/AdvancedDocumentAnalysis';

export default function DocumentsPage() {
  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 to-slate-100 dark:from-slate-900 dark:to-slate-800">
      <DashboardHeader />
      
      <main className="py-8">
        <AdvancedDocumentAnalysis />
      </main>
    </div>
  );
}