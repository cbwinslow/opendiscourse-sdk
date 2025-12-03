'use client'; // This is a client component

import { useEffect, useState } from 'react';

interface ProgressState {
  source: string;
  startDate: string; // ISO string
  endDate: string; // ISO string
  totalRecords: number;
  processedRecords: number;
  successfulInserts: number;
  failedRecords: number;
  duplicatesSkipped: number;
  currentPage: number;
  nextCursor: string;
  status: 'idle' | 'running' | 'paused' | 'completed' | 'failed' | 'fetching' | 'transforming' | 'persisting';
  lastUpdate: string; // ISO string
  estimatedCompletion: string; // ISO string
  metrics: {
    recordsPerSecond: number;
    averageLatency: number;
    errorRate: number;
  };
}

const ORCHESTRATOR_WORKER_URL = process.env.NEXT_PUBLIC_ORCHESTRATOR_WORKER_URL || 'YOUR_ORCHESTRATOR_WORKER_URL'; // Replace with your Orchestrator Worker URL

export default function DashboardPage() {
  const [progress, setProgress] = useState<ProgressState | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchStatus = async () => {
    setLoading(true);
    setError(null);
    try {
      const response = await fetch(`${ORCHESTRATOR_WORKER_URL}/get-status`);
      if (!response.ok) {
        throw new Error(`Failed to fetch status: ${response.statusText}`);
      }
      const data: ProgressState = await response.json();
      setProgress(data);
    } catch (err: any) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleAction = async (action: string, endpoint: string, method: string = 'GET', body?: any) => {
    setLoading(true);
    setError(null);
    try {
      const response = await fetch(`${ORCHESTRATOR_WORKER_URL}${endpoint}`, {
        method: method,
        headers: {
          'Content-Type': 'application/json',
        },
        body: body ? JSON.stringify(body) : undefined,
      });
      if (!response.ok) {
        const errorData = await response.json().catch(() => ({ message: response.statusText }));
        throw new Error(`Action '${action}' failed: ${errorData.message || response.statusText}`);
      }
      // Re-fetch status after action
      await fetchStatus();
    } catch (err: any) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchStatus();
    const interval = setInterval(fetchStatus, 5000); // Poll every 5 seconds
    return () => clearInterval(interval);
  }, []);

  if (loading && !progress) return <div className="p-4">Loading dashboard...</div>;
  if (error) return <div className="p-4 text-red-500">Error: {error}</div>;
  if (!progress) return <div className="p-4">No progress data available.</div>;

  return (
    <div className="min-h-screen bg-gray-100 p-8">
      <div className="max-w-4xl mx-auto bg-white rounded-lg shadow-md p-6">
        <h1 className="text-3xl font-bold text-gray-800 mb-6">Ingestion Dashboard</h1>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-8">
          <InfoCard title="Current Status" value={progress.status.toUpperCase()} color={getStatusColor(progress.status)} />
          <InfoCard title="Source" value={progress.source || 'N/A'} />
          <InfoCard title="Processed Records" value={progress.processedRecords.toLocaleString()} />
          <InfoCard title="Successful Inserts" value={progress.successfulInserts.toLocaleString()} />
          <InfoCard title="Failed Records" value={progress.failedRecords.toLocaleString()} />
          <InfoCard title="Duplicates Skipped" value={progress.duplicatesSkipped.toLocaleString()} />
          <InfoCard title="Last Update" value={new Date(progress.lastUpdate).toLocaleString()} />
          <InfoCard title="Estimated Completion" value={new Date(progress.estimatedCompletion).toLocaleString()} />
        </div>

        <div className="mb-8">
          <h2 className="text-2xl font-semibold text-gray-800 mb-4">Controls</h2>
          <div className="flex flex-wrap gap-4">
            <Button onClick={() => handleAction('Start', '/start-ingestion', 'POST', { source: 'generic', startDate: new Date().toISOString() })} label="Start Ingestion" />
            <Button onClick={() => handleAction('Pause', '/pause-ingestion')} label="Pause Ingestion" color="yellow" />
            <Button onClick={() => handleAction('Resume', '/resume-ingestion')} label="Resume Ingestion" color="green" />
            <Button onClick={() => handleAction('Reset', '/reset-job')} label="Reset Job" color="red" />
          </div>
        </div>

        <div className="mb-8">
          <h2 className="text-2xl font-semibold text-gray-800 mb-4">Run Specific Ingestion Jobs</h2>
          <div className="flex flex-wrap gap-4">
            <Button onClick={() => handleAction('Run Congress', '/run-congress-ingestion?apiEndpoint=member')} label="Run Congress Ingestion" />
            <Button onClick={() => handleAction('Run GovInfo', '/run-govinfo-ingestion?apiEndpoint=collections')} label="Run GovInfo Ingestion" />
            <Button onClick={() => handleAction('Run OpenStates', '/run-openstates-ingestion?apiEndpoint=legislators')} label="Run OpenStates Ingestion" />
          </div>
        </div>

        <div className="mb-8">
          <h2 className="text-2xl font-semibold text-gray-800 mb-4">Metrics</h2>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            <InfoCard title="Records/Sec" value={progress.metrics.recordsPerSecond.toFixed(2)} />
            <InfoCard title="Avg Latency (ms)" value={progress.metrics.averageLatency.toFixed(2)} />
            <InfoCard title="Error Rate (%)" value={progress.metrics.errorRate.toFixed(2)} />
          </div>
        </div>
      </div>
    </div>
  );
}

// Reusable Button Component
const Button = ({ onClick, label, color = 'blue' }: { onClick: () => void; label: string; color?: string }) => {
  const baseStyle = 'px-6 py-3 rounded-md text-white font-semibold shadow-sm hover:opacity-90 transition-opacity';
  let bgColor;
  switch (color) {
    case 'red': bgColor = 'bg-red-600'; break;
    case 'green': bgColor = 'bg-green-600'; break;
    case 'yellow': bgColor = 'bg-yellow-600'; break;
    default: bgColor = 'bg-blue-600';
  }
  return (
    <button className={`${baseStyle} ${bgColor}`} onClick={onClick}>
      {label}
    </button>
  );
};

// Reusable InfoCard Component
const InfoCard = ({ title, value, color }: { title: string; value: string | number; color?: string }) => {
  return (
    <div className="bg-gray-50 p-4 rounded-lg border border-gray-200">
      <h3 className="text-sm font-medium text-gray-500">{title}</h3>
      <p className={`mt-1 text-xl font-semibold ${color || 'text-gray-900'}`}>{value}</p>
    </div>
  );
};

// Helper to get status color
const getStatusColor = (status: ProgressState['status']) => {
  switch (status) {
    case 'running': return 'text-blue-600';
    case 'paused': return 'text-yellow-600';
    case 'completed': return 'text-green-600';
    case 'failed': return 'text-red-600';
    case 'fetching':
    case 'transforming':
    case 'persisting':
      return 'text-indigo-600';
    default: return 'text-gray-600';
  }
};
