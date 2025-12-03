import React, { useState, useCallback } from 'react';

interface SearchResult {
  id: string;
  title: string;
  content: string;
  score: number;
  source: string;
  entities: string[];
  highlights: string[];
  metadata: Record<string, unknown>;
}

interface SearchFilters {
  dateRange?: [string, string];
  entities?: string[];
  sources?: string[];
  minScore?: number;
}

interface SearchInterfaceProps {
  onSearch?: (query: string, filters: SearchFilters) => void;
  initialQuery?: string;
}

export function SearchInterface({ onSearch, initialQuery = '' }: SearchInterfaceProps) {
  const [query, setQuery] = useState(initialQuery);
  const [results, setResults] = useState<SearchResult[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [filters, setFilters] = useState<SearchFilters>({});
  const [totalResults, setTotalResults] = useState(0);
  const [currentPage, setCurrentPage] = useState(1);
  const [searchMode, setSearchMode] = useState<'semantic' | 'keyword' | 'hybrid'>('semantic');

  const performSearch = useCallback(async (searchQuery: string, searchFilters: SearchFilters, page = 1) => {
    if (!searchQuery.trim()) return;

    setLoading(true);
    setError(null);

    try {
      const searchParams = new URLSearchParams({
        q: searchQuery,
        mode: searchMode,
        page: page.toString(),
        limit: '10',
        ...Object.fromEntries(
          Object.entries(searchFilters).filter(([, v]) => v != null && v !== '')
        )
      });

      const response = await fetch(`/api/v1/search?${searchParams}`);
      
      if (!response.ok) {
        throw new Error(`Search failed: ${response.statusText}`);
      }

      const data = await response.json();
      
      setResults(data.results || []);
      setTotalResults(data.total || 0);
      setCurrentPage(page);

      if (onSearch) {
        onSearch(searchQuery, searchFilters);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Search failed');
      setResults([]);
    } finally {
      setLoading(false);
    }
  }, [searchMode, onSearch]);

  const handleSearch = useCallback((e: React.FormEvent) => {
    e.preventDefault();
    performSearch(query, filters, 1);
  }, [query, filters, performSearch]);

  const handlePageChange = useCallback((page: number) => {
    performSearch(query, filters, page);
  }, [query, filters, performSearch]);

  const highlightText = (text: string, highlights: string[]) => {
    if (!highlights.length) return text;
    
    let highlightedText = text;
    highlights.forEach(highlight => {
      const regex = new RegExp(`(${highlight})`, 'gi');
      highlightedText = highlightedText.replace(regex, '<mark>$1</mark>');
    });
    
    return highlightedText;
  };

  const totalPages = Math.ceil(totalResults / 10);

  return (
    <div className="w-full max-w-6xl mx-auto space-y-6">
      {/* Search Form */}
      <div className="bg-white rounded-lg border border-secondary-200 p-6">
        <form onSubmit={handleSearch} className="space-y-4">
          <div className="flex space-x-4">
            <div className="flex-1">
              <label htmlFor="search-query" className="block text-sm font-medium text-secondary-700 mb-2">
                Search Query
              </label>
              <div className="relative">
                <input
                  id="search-query"
                  type="text"
                  value={query}
                  onChange={(e) => setQuery(e.target.value)}
                  placeholder="Enter your search query..."
                  className="w-full px-4 py-3 border border-secondary-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
                />
                <button
                  type="submit"
                  disabled={loading || !query.trim()}
                  className="absolute right-2 top-1/2 transform -translate-y-1/2 p-2 text-primary-600 hover:text-primary-700 disabled:text-secondary-400"
                >
                  <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
                  </svg>
                </button>
              </div>
            </div>
          </div>

          {/* Search Mode Selection */}
          <div className="flex space-x-4">
            <div>
              <label className="block text-sm font-medium text-secondary-700 mb-2">Search Mode</label>
              <select
                value={searchMode}
                onChange={(e) => setSearchMode(e.target.value as typeof searchMode)}
                className="px-3 py-2 border border-secondary-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
              >
                <option value="semantic">Semantic Search</option>
                <option value="keyword">Keyword Search</option>
                <option value="hybrid">Hybrid Search</option>
              </select>
            </div>

            {/* Quick Filters */}
            <div className="flex-1">
              <label className="block text-sm font-medium text-secondary-700 mb-2">Quick Filters</label>
              <div className="flex space-x-2">
                <button
                  type="button"
                  onClick={() => setFilters({ ...filters, minScore: 0.8 })}
                  className={`px-3 py-2 text-sm rounded-lg border ${
                    filters.minScore === 0.8
                      ? 'bg-primary-100 border-primary-300 text-primary-800'
                      : 'bg-white border-secondary-300 text-secondary-700 hover:bg-secondary-50'
                  }`}
                >
                  High Relevance
                </button>
                <button
                  type="button"
                  onClick={() => setFilters({ ...filters, sources: ['congress.gov'] })}
                  className={`px-3 py-2 text-sm rounded-lg border ${
                    filters.sources?.includes('congress.gov')
                      ? 'bg-primary-100 border-primary-300 text-primary-800'
                      : 'bg-white border-secondary-300 text-secondary-700 hover:bg-secondary-50'
                  }`}
                >
                  Congress Only
                </button>
                <button
                  type="button"
                  onClick={() => setFilters({})}
                  className="px-3 py-2 text-sm rounded-lg border bg-white border-secondary-300 text-secondary-700 hover:bg-secondary-50"
                >
                  Clear Filters
                </button>
              </div>
            </div>
          </div>
        </form>
      </div>

      {/* Search Results */}
      {loading && (
        <div className="bg-white rounded-lg border border-secondary-200 p-8 text-center">
          <div className="inline-flex items-center space-x-2">
            <svg className="animate-spin w-5 h-5 text-primary-600" fill="none" viewBox="0 0 24 24">
              <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
              <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
            </svg>
            <span className="text-secondary-600">Searching...</span>
          </div>
        </div>
      )}

      {error && (
        <div className="bg-red-50 border border-red-200 rounded-lg p-4">
          <div className="flex items-center space-x-2">
            <svg className="w-5 h-5 text-red-500" fill="currentColor" viewBox="0 0 20 20">
              <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
            </svg>
            <span className="text-red-700">{error}</span>
          </div>
        </div>
      )}

      {!loading && !error && results.length === 0 && query && (
        <div className="bg-white rounded-lg border border-secondary-200 p-8 text-center">
          <svg className="mx-auto w-12 h-12 text-secondary-400 mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9.172 16.172a4 4 0 015.656 0M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
          </svg>
          <h3 className="text-lg font-semibold text-secondary-900 mb-2">No results found</h3>
          <p className="text-secondary-600">Try adjusting your search terms or filters</p>
        </div>
      )}

      {!loading && !error && results.length > 0 && (
        <div className="space-y-4">
          {/* Results Header */}
          <div className="flex items-center justify-between">
            <p className="text-sm text-secondary-600">
              Showing {((currentPage - 1) * 10) + 1}-{Math.min(currentPage * 10, totalResults)} of {totalResults} results
            </p>
            <div className="flex items-center space-x-2">
              <span className="text-sm text-secondary-600">Sort by:</span>
              <select className="text-sm border border-secondary-300 rounded px-2 py-1">
                <option value="relevance">Relevance</option>
                <option value="date">Date</option>
                <option value="title">Title</option>
              </select>
            </div>
          </div>

          {/* Results List */}
          <div className="space-y-4">
            {results.map((result) => (
              <div key={result.id} className="bg-white rounded-lg border border-secondary-200 p-6 hover:shadow-md transition-shadow">
                <div className="space-y-3">
                  <div className="flex items-start justify-between">
                    <h3 className="text-lg font-semibold text-secondary-900 hover:text-primary-600 cursor-pointer">
                      {result.title}
                    </h3>
                    <div className="flex items-center space-x-2">
                      <span className="text-xs bg-primary-100 text-primary-800 px-2 py-1 rounded-full">
                        Score: {(result.score * 100).toFixed(0)}%
                      </span>
                      <span className="text-xs bg-secondary-100 text-secondary-800 px-2 py-1 rounded-full">
                        {result.source}
                      </span>
                    </div>
                  </div>

                  <div 
                    className="text-secondary-700 line-clamp-3"
                    dangerouslySetInnerHTML={{ 
                      __html: highlightText(result.content, result.highlights) 
                    }}
                  />

                  {result.entities.length > 0 && (
                    <div className="flex items-center space-x-2">
                      <span className="text-xs font-medium text-secondary-600">Entities:</span>
                      <div className="flex flex-wrap gap-1">
                        {result.entities.slice(0, 5).map((entity, idx) => (
                          <span key={idx} className="text-xs bg-blue-100 text-blue-800 px-2 py-1 rounded">
                            {entity}
                          </span>
                        ))}
                        {result.entities.length > 5 && (
                          <span className="text-xs text-secondary-500">
                            +{result.entities.length - 5} more
                          </span>
                        )}
                      </div>
                    </div>
                  )}

                  <div className="flex items-center justify-between text-sm text-secondary-500">
                    <span>Document ID: {result.id}</span>
                    <div className="flex space-x-4">
                      <button className="text-primary-600 hover:text-primary-700 font-medium">
                        View Full Document
                      </button>
                      <button className="text-secondary-600 hover:text-secondary-700">
                        Export
                      </button>
                    </div>
                  </div>
                </div>
              </div>
            ))}
          </div>

          {/* Pagination */}
          {totalPages > 1 && (
            <div className="flex items-center justify-center space-x-2 mt-8">
              <button
                onClick={() => handlePageChange(currentPage - 1)}
                disabled={currentPage === 1}
                className="px-3 py-2 text-sm border border-secondary-300 rounded-lg disabled:opacity-50 disabled:cursor-not-allowed hover:bg-secondary-50"
              >
                Previous
              </button>
              
              {Array.from({ length: Math.min(5, totalPages) }, (_, i) => {
                const page = i + Math.max(1, currentPage - 2);
                if (page > totalPages) return null;
                
                return (
                  <button
                    key={page}
                    onClick={() => handlePageChange(page)}
                    className={`px-3 py-2 text-sm border rounded-lg ${
                      page === currentPage
                        ? 'bg-primary-600 text-white border-primary-600'
                        : 'border-secondary-300 hover:bg-secondary-50'
                    }`}
                  >
                    {page}
                  </button>
                );
              })}
              
              <button
                onClick={() => handlePageChange(currentPage + 1)}
                disabled={currentPage === totalPages}
                className="px-3 py-2 text-sm border border-secondary-300 rounded-lg disabled:opacity-50 disabled:cursor-not-allowed hover:bg-secondary-50"
              >
                Next
              </button>
            </div>
          )}
        </div>
      )}
    </div>
  );
}

export default SearchInterface;
