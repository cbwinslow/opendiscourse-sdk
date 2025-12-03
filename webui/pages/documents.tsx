import { useState, useEffect } from 'react';
import Layout from '../components/Layout';
import { FileText, Search, Calendar, Tag, ExternalLink, Filter } from 'lucide-react';

interface Document {
  id: string;
  title: string;
  content: string;
  source: string;
  document_type: string;
  metadata: Record<string, any>;
  created_at: string;
  updated_at: string;
  processed: boolean;
  entity_count?: number;
}

export default function DocumentsPage() {
  const [documents, setDocuments] = useState<Document[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');
  const [filterType, setFilterType] = useState('all');
  const [currentPage, setCurrentPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);

  useEffect(() => {
    fetchDocuments();
  }, [currentPage, filterType]);

  const fetchDocuments = async () => {
    try {
      const params = new URLSearchParams({
        page: currentPage.toString(),
        limit: '10',
        ...(filterType !== 'all' && { type: filterType }),
        ...(searchTerm && { search: searchTerm }),
      });

      const response = await fetch(`/api/backend/documents?${params}`);
      const data = await response.json();
      
      setDocuments(data.documents || []);
      setTotalPages(Math.ceil((data.total || 0) / 10));
    } catch (error) {
      console.error('Error fetching documents:', error);
      // Mock data for demo
      setDocuments([
        {
          id: '1',
          title: 'Climate Change Policy Framework Act',
          content: 'This bill establishes a comprehensive framework for addressing climate change through federal policy coordination...',
          source: 'Congressional Bills',
          document_type: 'bill',
          metadata: { congress: 118, session: 1 },
          created_at: '2024-01-15T10:30:00Z',
          updated_at: '2024-01-15T10:30:00Z',
          processed: true,
          entity_count: 25,
        },
        {
          id: '2',
          title: 'Federal Infrastructure Investment Guidelines',
          content: 'Guidance for federal agencies on infrastructure investment priorities and evaluation criteria...',
          source: 'Federal Register',
          document_type: 'regulation',
          metadata: { agency: 'DOT', docket: 'DOT-2024-0001' },
          created_at: '2024-01-14T16:45:00Z',
          updated_at: '2024-01-14T16:45:00Z',
          processed: true,
          entity_count: 18,
        },
      ]);
    } finally {
      setLoading(false);
    }
  };

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault();
    setCurrentPage(1);
    fetchDocuments();
  };

  const getDocumentTypeColor = (type: string) => {
    switch (type) {
      case 'bill':
        return 'bg-blue-100 text-blue-800';
      case 'regulation':
        return 'bg-green-100 text-green-800';
      case 'record':
        return 'bg-purple-100 text-purple-800';
      default:
        return 'bg-gray-100 text-gray-800';
    }
  };

  return (
    <Layout title="Documents">
      <div className="max-w-6xl mx-auto space-y-6">
        {/* Header */}
        <div className="bg-white p-6 rounded-lg shadow">
          <h1 className="text-2xl font-bold text-gray-900 mb-2">
            Document Library
          </h1>
          <p className="text-gray-600">
            Browse and search through all processed political documents in the system.
          </p>
        </div>

        {/* Search and Filters */}
        <div className="bg-white p-6 rounded-lg shadow">
          <form onSubmit={handleSearch} className="space-y-4">
            <div className="flex space-x-4">
              <div className="flex-1">
                <input
                  type="text"
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                  placeholder="Search documents..."
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                />
              </div>
              
              <select
                value={filterType}
                onChange={(e) => setFilterType(e.target.value)}
                className="px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
              >
                <option value="all">All Types</option>
                <option value="bill">Bills</option>
                <option value="regulation">Regulations</option>
                <option value="record">Records</option>
              </select>
              
              <button
                type="submit"
                className="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 flex items-center"
              >
                <Search className="h-4 w-4 mr-2" />
                Search
              </button>
            </div>
          </form>
        </div>

        {/* Document List */}
        <div className="bg-white rounded-lg shadow">
          {loading ? (
            <div className="p-6 text-center">
              <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mx-auto"></div>
              <p className="text-gray-500 mt-2">Loading documents...</p>
            </div>
          ) : documents.length === 0 ? (
            <div className="p-6 text-center">
              <FileText className="h-12 w-12 text-gray-400 mx-auto mb-4" />
              <h3 className="text-lg font-medium text-gray-900 mb-2">No documents found</h3>
              <p className="text-gray-600">
                Try adjusting your search terms or upload new documents.
              </p>
            </div>
          ) : (
            <div className="divide-y divide-gray-200">
              {documents.map((doc) => (
                <div key={doc.id} className="p-6">
                  <div className="flex justify-between items-start">
                    <div className="flex-1">
                      <div className="flex items-center mb-2">
                        <h3 className="text-lg font-medium text-gray-900 mr-3">
                          {doc.title}
                        </h3>
                        <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${getDocumentTypeColor(doc.document_type)}`}>
                          {doc.document_type}
                        </span>
                        {doc.processed && (
                          <span className="ml-2 inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-green-100 text-green-800">
                            Processed
                          </span>
                        )}
                      </div>
                      
                      <p className="text-gray-700 mb-3 line-clamp-2">
                        {doc.content.substring(0, 200)}...
                      </p>
                      
                      <div className="grid grid-cols-1 md:grid-cols-4 gap-4 text-sm text-gray-500">
                        <div className="flex items-center">
                          <Tag className="h-4 w-4 mr-1" />
                          <span>Source: {doc.source}</span>
                        </div>
                        <div className="flex items-center">
                          <Calendar className="h-4 w-4 mr-1" />
                          <span>
                            {new Date(doc.created_at).toLocaleDateString()}
                          </span>
                        </div>
                        {doc.entity_count && (
                          <div className="flex items-center">
                            <FileText className="h-4 w-4 mr-1" />
                            <span>Entities: {doc.entity_count}</span>
                          </div>
                        )}
                        <div className="flex items-center">
                          <span className={`w-2 h-2 rounded-full mr-2 ${doc.processed ? 'bg-green-500' : 'bg-yellow-500'}`}></span>
                          <span>{doc.processed ? 'Ready' : 'Processing'}</span>
                        </div>
                      </div>
                      
                      {/* Metadata */}
                      {doc.metadata && Object.keys(doc.metadata).length > 0 && (
                        <div className="mt-3 flex flex-wrap gap-2">
                          {Object.entries(doc.metadata).slice(0, 3).map(([key, value]) => (
                            <span
                              key={key}
                              className="inline-flex items-center px-2 py-1 rounded text-xs font-medium bg-gray-100 text-gray-800"
                            >
                              {key}: {String(value)}
                            </span>
                          ))}
                        </div>
                      )}
                    </div>
                    
                    <div className="ml-4 flex space-x-2">
                      <button className="inline-flex items-center px-3 py-1 border border-gray-300 shadow-sm text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50">
                        <ExternalLink className="h-4 w-4 mr-1" />
                        View
                      </button>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Pagination */}
        {totalPages > 1 && (
          <div className="bg-white px-4 py-3 flex items-center justify-between border-t border-gray-200 sm:px-6 rounded-lg shadow">
            <div className="flex-1 flex justify-between sm:hidden">
              <button
                onClick={() => setCurrentPage(Math.max(1, currentPage - 1))}
                disabled={currentPage === 1}
                className="relative inline-flex items-center px-4 py-2 border border-gray-300 text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 disabled:opacity-50"
              >
                Previous
              </button>
              <button
                onClick={() => setCurrentPage(Math.min(totalPages, currentPage + 1))}
                disabled={currentPage === totalPages}
                className="ml-3 relative inline-flex items-center px-4 py-2 border border-gray-300 text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 disabled:opacity-50"
              >
                Next
              </button>
            </div>
            <div className="hidden sm:flex-1 sm:flex sm:items-center sm:justify-between">
              <div>
                <p className="text-sm text-gray-700">
                  Page <span className="font-medium">{currentPage}</span> of{' '}
                  <span className="font-medium">{totalPages}</span>
                </p>
              </div>
              <div>
                <nav className="relative z-0 inline-flex rounded-md shadow-sm -space-x-px">
                  <button
                    onClick={() => setCurrentPage(Math.max(1, currentPage - 1))}
                    disabled={currentPage === 1}
                    className="relative inline-flex items-center px-2 py-2 rounded-l-md border border-gray-300 bg-white text-sm font-medium text-gray-500 hover:bg-gray-50 disabled:opacity-50"
                  >
                    Previous
                  </button>
                  <button
                    onClick={() => setCurrentPage(Math.min(totalPages, currentPage + 1))}
                    disabled={currentPage === totalPages}
                    className="relative inline-flex items-center px-2 py-2 rounded-r-md border border-gray-300 bg-white text-sm font-medium text-gray-500 hover:bg-gray-50 disabled:opacity-50"
                  >
                    Next
                  </button>
                </nav>
              </div>
            </div>
          </div>
        )}
      </div>
    </Layout>
  );
}