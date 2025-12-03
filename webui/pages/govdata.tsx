import { useState, useEffect } from 'react';
import Layout from '../components/Layout';
import { Database, Download, Play, CheckCircle, Clock, AlertCircle } from 'lucide-react';

interface DataSource {
  id: string;
  name: string;
  description: string;
  url: string;
  status: 'available' | 'syncing' | 'error';
  last_sync: string;
  document_count: number;
}

export default function GovDataPage() {
  const [sources, setSources] = useState<DataSource[]>([]);
  const [loading, setLoading] = useState(true);
  const [syncing, setSyncing] = useState<string | null>(null);

  useEffect(() => {
    fetchSources();
  }, []);

  const fetchSources = async () => {
    try {
      const response = await fetch('/api/backend/govdata/sources');
      const data = await response.json();
      setSources(data.sources || []);
    } catch (error) {
      console.error('Error fetching sources:', error);
      // Mock data for demo
      setSources([
        {
          id: 'congress-bills',
          name: 'Congressional Bills',
          description: 'Bills from the current and recent sessions of Congress',
          url: 'https://api.govinfo.gov/collections/BILLS',
          status: 'available',
          last_sync: '2024-01-15T10:30:00Z',
          document_count: 1250,
        },
        {
          id: 'congressional-record',
          name: 'Congressional Record',
          description: 'Daily proceedings and debates of Congress',
          url: 'https://api.govinfo.gov/collections/CREC',
          status: 'available',
          last_sync: '2024-01-15T08:15:00Z',
          document_count: 892,
        },
        {
          id: 'federal-register',
          name: 'Federal Register',
          description: 'Federal rules, proposed rules, and notices',
          url: 'https://api.govinfo.gov/collections/FR',
          status: 'syncing',
          last_sync: '2024-01-14T16:45:00Z',
          document_count: 2341,
        },
      ]);
    } finally {
      setLoading(false);
    }
  };

  const handleSync = async (sourceId: string) => {
    setSyncing(sourceId);
    try {
      const response = await fetch('/api/backend/govdata/ingest', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ source: sourceId }),
      });

      if (!response.ok) {
        throw new Error('Sync failed');
      }

      // Refresh sources after sync
      await fetchSources();
    } catch (error) {
      console.error('Sync error:', error);
    } finally {
      setSyncing(null);
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'available':
        return <CheckCircle className="h-5 w-5 text-green-500" />;
      case 'syncing':
        return <Clock className="h-5 w-5 text-yellow-500 animate-spin" />;
      case 'error':
        return <AlertCircle className="h-5 w-5 text-red-500" />;
      default:
        return <Clock className="h-5 w-5 text-gray-500" />;
    }
  };

  const getStatusText = (status: string) => {
    switch (status) {
      case 'available':
        return 'Available';
      case 'syncing':
        return 'Syncing...';
      case 'error':
        return 'Error';
      default:
        return 'Unknown';
    }
  };

  return (
    <Layout title="Government Data">
      <div className="max-w-6xl mx-auto space-y-6">
        {/* Header */}
        <div className="bg-white p-6 rounded-lg shadow">
          <h1 className="text-2xl font-bold text-gray-900 mb-2">
            Government Data Sources
          </h1>
          <p className="text-gray-600">
            Sync and analyze documents from official government sources including Congress, Federal Register, and more.
          </p>
        </div>

        {/* Data Sources */}
        <div className="bg-white rounded-lg shadow">
          <div className="px-6 py-4 border-b">
            <h2 className="text-lg font-semibold text-gray-900">Available Sources</h2>
          </div>
          
          {loading ? (
            <div className="p-6 text-center">
              <Clock className="h-8 w-8 text-gray-400 mx-auto mb-2 animate-spin" />
              <p className="text-gray-500">Loading sources...</p>
            </div>
          ) : (
            <div className="divide-y divide-gray-200">
              {sources.map((source) => (
                <div key={source.id} className="p-6">
                  <div className="flex justify-between items-start">
                    <div className="flex-1">
                      <div className="flex items-center mb-2">
                        <Database className="h-5 w-5 text-blue-600 mr-2" />
                        <h3 className="text-lg font-medium text-gray-900">
                          {source.name}
                        </h3>
                        <div className="ml-3 flex items-center">
                          {getStatusIcon(source.status)}
                          <span className={`ml-1 text-sm ${
                            source.status === 'available' ? 'text-green-600' :
                            source.status === 'syncing' ? 'text-yellow-600' :
                            'text-red-600'
                          }`}>
                            {getStatusText(source.status)}
                          </span>
                        </div>
                      </div>
                      
                      <p className="text-gray-600 mb-3">{source.description}</p>
                      
                      <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-sm text-gray-500">
                        <div>
                          <span className="font-medium">Documents:</span>
                          <span className="ml-2">{source.document_count.toLocaleString()}</span>
                        </div>
                        <div>
                          <span className="font-medium">Last Sync:</span>
                          <span className="ml-2">
                            {new Date(source.last_sync).toLocaleDateString()}
                          </span>
                        </div>
                        <div>
                          <span className="font-medium">Source:</span>
                          <a
                            href={source.url}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="ml-2 text-blue-600 hover:text-blue-800"
                          >
                            govinfo.gov
                          </a>
                        </div>
                      </div>
                    </div>
                    
                    <div className="ml-4">
                      <button
                        onClick={() => handleSync(source.id)}
                        disabled={syncing === source.id || source.status === 'syncing'}
                        className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md shadow-sm text-white bg-blue-600 hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
                      >
                        {syncing === source.id ? (
                          <>
                            <Clock className="h-4 w-4 mr-2 animate-spin" />
                            Syncing...
                          </>
                        ) : (
                          <>
                            <Download className="h-4 w-4 mr-2" />
                            Sync Now
                          </>
                        )}
                      </button>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Sync Instructions */}
        <div className="bg-blue-50 border border-blue-200 rounded-lg p-6">
          <h3 className="text-lg font-medium text-blue-900 mb-3">About Government Data Sync</h3>
          <ul className="space-y-2 text-sm text-blue-800">
            <li className="flex items-start">
              <Play className="h-4 w-4 mt-0.5 mr-2 flex-shrink-0" />
              <span>Data is synced from official government APIs including govinfo.gov</span>
            </li>
            <li className="flex items-start">
              <Play className="h-4 w-4 mt-0.5 mr-2 flex-shrink-0" />
              <span>Documents are processed for entity extraction and semantic analysis</span>
            </li>
            <li className="flex items-start">
              <Play className="h-4 w-4 mt-0.5 mr-2 flex-shrink-0" />
              <span>Sync frequency can be configured for automatic updates</span>
            </li>
            <li className="flex items-start">
              <Play className="h-4 w-4 mt-0.5 mr-2 flex-shrink-0" />
              <span>All documents are indexed for search and analysis</span>
            </li>
          </ul>
        </div>
      </div>
    </Layout>
  );
}