'use client';

import { DashboardHeader } from '@/components/dashboard/header';
import { AdvancedRAGInterface } from '@/components/rag/AdvancedRAGInterface';

export default function ChatPage() {
  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 to-slate-100 dark:from-slate-900 dark:to-slate-800">
      <DashboardHeader />
      
      <main className="py-8">
        <AdvancedRAGInterface />
      </main>
    </div>
  );
}