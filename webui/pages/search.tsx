import { useState } from 'react';
import Layout from '../components/Layout';
import { Search, FileText, User, MapPin, Calendar, ExternalLink } from 'lucide-react';

interface Answer {
  answer: string;
  sources?: { content: string; source: string }[];
}

interface SearchResult {
  id: string;
  title: string;
  content: string;
  source: string;
  score: number;
  entities: any[];
  metadata: any;
  created_at: string;
}

export default function SearchPage() {
  const [question, setQuestion] = useState('');
  const [result, setResult] = useState<Answer | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSearch = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!question.trim()) return;

    setLoading(true);
    setError(null);
    setResult(null);

    try {
      const response = await fetch('/api/query', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ question }),
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.error || data.detail || 'Search failed');
      }

      setResult(data);
    } catch (err: any) {
      setError(err.message);
      setResult({ answer: `Error: ${err.message}` });
    } finally {
      setLoading(false);
    }
  };

  return (
    <Layout title="Semantic Search">
      <div className="max-w-6xl mx-auto space-y-6">
        {/* Header */}
        <div className="bg-white p-6 rounded-lg shadow">
          <h1 className="text-2xl font-bold text-gray-900 mb-2">
            Document Search & Analysis
          </h1>
          <p className="text-gray-600">
            Search through political documents using advanced semantic understanding and RAG capabilities.
          </p>
        </div>

        {/* Search Form */}
        <div className="bg-white p-6 rounded-lg shadow">
          <form onSubmit={handleSearch} className="space-y-4">
            <div className="flex space-x-4">
              <div className="flex-1">
                <input
                  type="text"
                  value={question}
                  onChange={(e) => setQuestion(e.target.value)}
                  placeholder="Ask a question about political documents..."
                  className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                />
              </div>
              
              <button
                type="submit"
                disabled={loading || !question.trim()}
                className="px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed flex items-center"
              >
                <Search className="h-5 w-5 mr-2" />
                {loading ? 'Searching...' : 'Ask'}
              </button>
            </div>
          </form>
        </div>

        {/* Error Message */}
        {error && (
          <div className="bg-red-50 border border-red-200 rounded-lg p-4">
            <p className="text-red-800">{error}</p>
          </div>
        )}

        {/* Results */}
        {result && (
          <div className="bg-white p-6 rounded-lg shadow">
            <h2 className="text-xl font-semibold text-gray-900 mb-4">Answer</h2>
            
            <div className="prose max-w-none mb-6">
              <p className="text-gray-700 leading-relaxed">{result.answer}</p>
            </div>

            {/* Sources */}
            {result.sources && result.sources.length > 0 && (
              <div>
                <h3 className="text-lg font-semibold text-gray-900 mb-3">Sources</h3>
                <div className="space-y-3">
                  {result.sources.map((source, index) => (
                    <div key={index} className="border border-gray-200 rounded-lg p-4">
                      <div className="flex justify-between items-start mb-2">
                        <h4 className="font-medium text-gray-900">{source.source}</h4>
                        <button className="inline-flex items-center text-blue-600 hover:text-blue-800 text-sm">
                          <ExternalLink className="h-4 w-4 mr-1" />
                          View
                        </button>
                      </div>
                      <p className="text-gray-700 text-sm">{source.content}</p>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        )}

        {/* Empty State */}
        {!loading && !result && !error && (
          <div className="bg-gray-50 p-8 rounded-lg text-center">
            <Search className="h-12 w-12 text-gray-400 mx-auto mb-4" />
            <h3 className="text-lg font-medium text-gray-900 mb-2">Ask a question to get started</h3>
            <p className="text-gray-600">
              Use natural language to search through political documents and get intelligent answers.
            </p>
          </div>
        )}

        {/* Search Tips */}
        <div className="bg-blue-50 border border-blue-200 rounded-lg p-6">
          <h3 className="text-lg font-medium text-blue-900 mb-3">Search Tips</h3>
          <ul className="space-y-2 text-sm text-blue-800">
            <li>• Ask natural language questions like "What policies affect climate change?"</li>
            <li>• Be specific about the information you're looking for</li>
            <li>• Search results use advanced RAG (Retrieval Augmented Generation) for accurate answers</li>
            <li>• Sources are provided to verify the information</li>
          </ul>
        </div>
      </div>
    </Layout>
  );
}
