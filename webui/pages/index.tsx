import { useState, useEffect } from 'react';
import Layout from '../components/Layout';
import { FileText, Users, Database, TrendingUp, Activity, Clock } from 'lucide-react';
import { documentApi, ragApi } from '../lib/api';

interface DashboardStats {
  totalDocuments: number;
  processedDocuments: number;
  totalEntities: number;
  recentQueries: number;
}

export default function Home() {
  const [stats, setStats] = useState<DashboardStats>({
    totalDocuments: 0,
    processedDocuments: 0,
    totalEntities: 0,
    recentQueries: 0,
  });
  const [loading, setLoading] = useState(true);
  const [recentActivity, setRecentActivity] = useState<any[]>([]);

  useEffect(() => {
    fetchDashboardData();
  }, []);

  const fetchDashboardData = async () => {
    try {
      // Fetch dashboard statistics
      const [docsResponse, queryHistory] = await Promise.all([
        documentApi.list({ limit: 1000 }),
        ragApi.history(),
      ]);

      const documents = docsResponse.data.documents || [];
      const processed = documents.filter((doc: any) => doc.processed).length;

      setStats({
        totalDocuments: documents.length,
        processedDocuments: processed,
        totalEntities: 0, // Will be calculated from entity extraction
        recentQueries: queryHistory.data.queries?.length || 0,
      });

      setRecentActivity(queryHistory.data.queries?.slice(0, 5) || []);
    } catch (error) {
      console.error('Error fetching dashboard data:', error);
    } finally {
      setLoading(false);
    }
  };

  const statCards = [
    {
      title: 'Total Documents',
      value: stats.totalDocuments,
      icon: FileText,
      color: 'text-blue-600',
      bgColor: 'bg-blue-50',
    },
    {
      title: 'Processed Documents',
      value: stats.processedDocuments,
      icon: Database,
      color: 'text-green-600',
      bgColor: 'bg-green-50',
    },
    {
      title: 'Extracted Entities',
      value: stats.totalEntities,
      icon: Users,
      color: 'text-purple-600',
      bgColor: 'bg-purple-50',
    },
    {
      title: 'Recent Queries',
      value: stats.recentQueries,
      icon: TrendingUp,
      color: 'text-orange-600',
      bgColor: 'bg-orange-50',
    },
  ];

  return (
    <Layout title="Dashboard">
      <div className="space-y-6">
        {/* Welcome Section */}
        <div className="bg-white p-6 rounded-lg shadow">
          <h1 className="text-2xl font-bold text-gray-900 mb-2">
            Welcome to OpenDiscourse
          </h1>
          <p className="text-gray-600">
            Analyze political documents with advanced NLP and AI-powered insights.
            Upload documents, extract entities, and discover meaningful patterns in political discourse.
          </p>
        </div>

        {/* Statistics Cards */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          {statCards.map((card, index) => (
            <div key={index} className="bg-white p-6 rounded-lg shadow">
              <div className="flex items-center">
                <div className={`p-3 rounded-lg ${card.bgColor}`}>
                  <card.icon className={`h-6 w-6 ${card.color}`} />
                </div>
                <div className="ml-4">
                  <p className="text-sm font-medium text-gray-600">{card.title}</p>
                  <p className="text-2xl font-bold text-gray-900">
                    {loading ? '...' : card.value.toLocaleString()}
                  </p>
                </div>
              </div>
            </div>
          ))}
        </div>

        {/* Recent Activity and Quick Actions */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Recent Activity */}
          <div className="bg-white p-6 rounded-lg shadow">
            <div className="flex items-center mb-4">
              <Activity className="h-5 w-5 text-gray-500 mr-2" />
              <h3 className="text-lg font-semibold text-gray-900">Recent Activity</h3>
            </div>
            {recentActivity.length > 0 ? (
              <div className="space-y-3">
                {recentActivity.map((activity, index) => (
                  <div key={index} className="flex items-center p-3 bg-gray-50 rounded-lg">
                    <Clock className="h-4 w-4 text-gray-400 mr-3" />
                    <div>
                      <p className="text-sm font-medium text-gray-900">
                        Query: "{activity.question?.substring(0, 50)}..."
                      </p>
                      <p className="text-xs text-gray-500">
                        {new Date(activity.created_at).toLocaleDateString()}
                      </p>
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <p className="text-gray-500">No recent activity</p>
            )}
          </div>

          {/* Quick Actions */}
          <div className="bg-white p-6 rounded-lg shadow">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">Quick Actions</h3>
            <div className="space-y-3">
              <a
                href="/upload"
                className="flex items-center p-3 border border-gray-200 rounded-lg hover:bg-gray-50 transition-colors"
              >
                <FileText className="h-5 w-5 text-blue-600 mr-3" />
                <div>
                  <p className="font-medium text-gray-900">Upload Document</p>
                  <p className="text-sm text-gray-500">Add new documents for analysis</p>
                </div>
              </a>
              
              <a
                href="/search"
                className="flex items-center p-3 border border-gray-200 rounded-lg hover:bg-gray-50 transition-colors"
              >
                <Users className="h-5 w-5 text-green-600 mr-3" />
                <div>
                  <p className="font-medium text-gray-900">Semantic Search</p>
                  <p className="text-sm text-gray-500">Find relevant documents and entities</p>
                </div>
              </a>
              
              <a
                href="/govdata"
                className="flex items-center p-3 border border-gray-200 rounded-lg hover:bg-gray-50 transition-colors"
              >
                <Database className="h-5 w-5 text-purple-600 mr-3" />
                <div>
                  <p className="font-medium text-gray-900">Government Data</p>
                  <p className="text-sm text-gray-500">Ingest from govinfo.gov</p>
                </div>
              </a>
            </div>
          </div>
        </div>
      </div>
    </Layout>
  );
}
