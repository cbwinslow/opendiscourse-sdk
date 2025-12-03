import { Metadata } from 'next';
import { Suspense } from 'react';
import { DashboardHeader } from '@/components/dashboard/header';
import { DashboardStats } from '@/components/dashboard/stats';
import { FeatureGrid } from '@/components/dashboard/feature-grid';
import { RecentActivity } from '@/components/dashboard/recent-activity';
import { SystemStatus } from '@/components/dashboard/system-status';
import { QuickActions } from '@/components/dashboard/quick-actions';
import { LoadingSpinner } from '@/components/ui/loading-spinner';

export const metadata: Metadata = {
  title: 'Dashboard',
  description: 'OpenDiscourse enterprise dashboard for political document analysis and management.',
};

async function getDashboardData() {
  // In a real app, this would fetch from your API
  // For now, we'll return mock data
  return {
    stats: [
      { label: 'Documents Processed', value: '10,247', change: '+12%' },
      { label: 'RAG Queries', value: '3,891', change: '+8%' },
      { label: 'Active Users', value: '156', change: '+5%' },
      { label: 'Entities Extracted', value: '47,293', change: '+15%' },
    ],
    recentQueries: [
      { query: "What is the budget allocation for healthcare?", time: "2 minutes ago" },
      { query: "Find bills related to infrastructure spending", time: "15 minutes ago" },
      { query: "Committee assignments for education policy", time: "1 hour ago" },
    ],
    systemStatus: [
      { service: "RAG Service", status: "Operational", uptime: "99.9%" },
      { service: "Document Processor", status: "Operational", uptime: "99.7%" },
      { service: "Vector Database", status: "Operational", uptime: "99.8%" },
      { service: "API Gateway", status: "Operational", uptime: "99.9%" },
    ]
  };
}

export default async function DashboardPage() {
  const data = await getDashboardData();

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 to-slate-100 dark:from-slate-900 dark:to-slate-800">
      <DashboardHeader />
      
      <main className="container mx-auto px-4 py-8 space-y-8">
        <div className="space-y-2">
          <h1 className="text-3xl font-bold tracking-tight text-slate-900 dark:text-slate-100">
            Welcome to OpenDiscourse
          </h1>
          <p className="text-slate-600 dark:text-slate-400">
            Enterprise-grade platform for government document analysis and retrieval
          </p>
        </div>

        {/* Stats Overview */}
        <Suspense fallback={<LoadingSpinner />}>
          <DashboardStats stats={data.stats} />
        </Suspense>

        {/* Feature Grid */}
        <Suspense fallback={<LoadingSpinner />}>
          <FeatureGrid />
        </Suspense>

        {/* Activity and Status */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
          <Suspense fallback={<LoadingSpinner />}>
            <RecentActivity queries={data.recentQueries} />
          </Suspense>
          
          <Suspense fallback={<LoadingSpinner />}>
            <SystemStatus services={data.systemStatus} />
          </Suspense>
        </div>

        {/* Quick Actions */}
        <Suspense fallback={<LoadingSpinner />}>
          <QuickActions />
        </Suspense>
      </main>
    </div>
  );
}