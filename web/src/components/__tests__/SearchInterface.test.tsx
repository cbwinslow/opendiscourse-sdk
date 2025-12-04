/**
 * ================================================================================
 * File: SearchInterface.test.tsx
 * Author: OpenDiscourse Contributors
 * Created: 2025-12-04
 * Last Modified: 2025-12-04
 * Version: 1.0.0
 *
 * Description:
 *     Comprehensive Jest tests for SearchInterface component.
 *     Tests search functionality, result handling, and user interactions.
 *
 * ================================================================================
 */

import '@testing-library/jest-dom';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import SearchInterface from '../SearchInterface';

// Mock Next.js components
jest.mock('next/image', () => ({
  __esModule: true,
  default: (props) => {
    return <img {...props} data-testid="mock-image" />;
  },
}));

// Mock API calls
global.fetch = jest.fn();

const mockSearchResults = {
  results: [
    {
      id: 'result-1',
      title: 'Search Result 1',
      snippet: 'This is a snippet for result 1...',
      relevanceScore: 0.9,
      source: 'congress.gov',
      type: 'bill',
      url: 'https://example.com/result/1',
      metadata: {
        congress: 118,
        state: 'CA',
        party: 'D',
      },
    },
    {
      id: 'result-2',
      title: 'Search Result 2',
      snippet: 'This is a snippet for result 2...',
      relevanceScore: 0.85,
      source: 'openstates.org',
      type: 'member',
      url: 'https://example.com/result/2',
      metadata: {
        congress: 117,
        state: 'TX',
        party: 'R',
      },
    },
  ],
  totalResults: 2,
  searchTime: 0.25,
  query: 'test query',
  facets: {
    type: { bill: 1, member: 1 },
    source: { 'congress.gov': 1, 'openstates.org': 1 },
    congress: { 118: 1, 117: 1 },
  },
};

describe('SearchInterface', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    global.fetch = jest.fn();
  });

  describe('Rendering', () => {
    test('renders search interface with all elements', () => {
      render(<SearchInterface />);

      expect(screen.getByRole('search')).toBeInTheDocument();
      expect(screen.getByPlaceholderText(/search legislation/i)).toBeInTheDocument();
      expect(screen.getByLabelText(/search/i)).toBeInTheDocument();
      expect(screen.getByRole('button', { name: /search/i })).toBeInTheDocument();
    });

    test('renders with custom placeholder', () => {
      const customPlaceholder = 'Search bills and legislation';
      render(<SearchInterface placeholder={customPlaceholder} />);

      expect(screen.getByPlaceholderText(customPlaceholder)).toBeInTheDocument();
    });

    test('renders result count display', () => {
      render(<SearchInterface />);

      expect(screen.getByText(/no results/i)).toBeInTheDocument();
    });
  });

  describe('Search Functionality', () => {
    test('updates query when user types', async () => {
      const user = userEvent.setup();
      render(<SearchInterface />);

      const searchInput = screen.getByPlaceholderText(/search legislation/i);
      await user.type(searchInput, 'test query');

      expect(searchInput).toHaveValue('test query');
    });

    test('triggers search on button click', async () => {
      const user = userEvent.setup();
      global.fetch.mockResolvedValueOnce({
        ok: true,
        json: async () => mockSearchResults,
      });

      render(<SearchInterface />);

      const searchInput = screen.getByPlaceholderText(/search legislation/i);
      const searchButton = screen.getByRole('button', { name: /search/i });

      await user.type(searchInput, 'test query');
      await user.click(searchButton);

      await waitFor(() => {
        expect(global.fetch).toHaveBeenCalledWith(
          expect.stringContaining('/api/search'),
          expect.objectContaining({
            method: 'POST',
            body: JSON.stringify({ query: 'test query', filters: {} }),
          })
        );
      });
    });

    test('displays loading state during search', async () => {
      const user = userEvent.setup();
      const loadingPromise = new Promise(resolve => setTimeout(() => resolve(mockSearchResults), 100));
      global.fetch.mockReturnValueOnce(loadingPromise);

      render(<SearchInterface />);

      const searchInput = screen.getByPlaceholderText(/search legislation/i);
      const searchButton = screen.getByRole('button', { name: /search/i });

      await user.type(searchInput, 'test query');
      await user.click(searchButton);

      await waitFor(() => {
        expect(screen.getByText(/searching/i)).toBeInTheDocument();
      });
    });
  });

  describe('Search Results', () => {
    beforeEach(() => {
      global.fetch.mockResolvedValueOnce({
        ok: true,
        json: async () => mockSearchResults,
      });
    });

    test('displays search results', async () => {
      const user = userEvent.setup();
      render(<SearchInterface />);

      const searchInput = screen.getByPlaceholderText(/search legislation/i);
      const searchButton = screen.getByRole('button', { name: /search/i });

      await user.type(searchInput, 'test query');
      await user.click(searchButton);

      await waitFor(() => {
        expect(screen.getByText(/2 results found/i)).toBeInTheDocument();
      });

      // Check for result items
      expect(screen.getByText('Search Result 1')).toBeInTheDocument();
      expect(screen.getByText('Search Result 2')).toBeInTheDocument();
    });

    test('displays result snippets', async () => {
      const user = userEvent.setup();
      render(<SearchInterface />);

      const searchInput = screen.getByPlaceholderText(/search legislation/i);
      const searchButton = screen.getByRole('button', { name: /search/i });

      await user.type(searchInput, 'test query');
      await user.click(searchButton);

      await waitFor(() => {
        expect(screen.getByText(/this is a snippet for result 1/i)).toBeInTheDocument();
      });
    });
  });

  describe('Error Handling', () => {
    test('displays error message on search failure', async () => {
      const user = userEvent.setup();
      global.fetch.mockRejectedValueOnce(new Error('Network error'));

      render(<SearchInterface />);

      const searchInput = screen.getByPlaceholderText(/search legislation/i);
      const searchButton = screen.getByRole('button', { name: /search/i });

      await user.type(searchInput, 'test query');
      await user.click(searchButton);

      await waitFor(() => {
        expect(screen.getByText(/search failed/i)).toBeInTheDocument();
      });
    });

    test('handles API errors gracefully', async () => {
      const user = userEvent.setup();
      global.fetch.mockResolvedValueOnce({
        ok: false,
        status: 500,
        json: async () => ({ error: 'Internal server error' }),
      });

      render(<SearchInterface />);

      const searchInput = screen.getByPlaceholderText(/search legislation/i);
      const searchButton = screen.getByRole('button', { name: /search/i });

      await user.type(searchInput, 'test query');
      await user.click(searchButton);

      await waitFor(() => {
        expect(screen.getByText(/search failed/i)).toBeInTheDocument();
      });
    });
  });

  describe('Accessibility', () => {
    test('has proper ARIA labels', () => {
      render(<SearchInterface />);

      expect(screen.getByRole('search')).toHaveAttribute('aria-label', 'Search legislation');
      expect(screen.getByLabelText(/search/i)).toHaveAttribute('placeholder', 'Search legislation');
    });

    test('supports keyboard navigation', async () => {
      const user = userEvent.setup();
      render(<SearchInterface />);

      const searchInput = screen.getByPlaceholderText(/search legislation/i);
      const searchButton = screen.getByRole('button', { name: /search/i });

      // Navigate using Tab
      await user.tab();
      expect(searchInput).toHaveFocus();

      await user.tab();
      expect(searchButton).toHaveFocus();
    });
  });
});
