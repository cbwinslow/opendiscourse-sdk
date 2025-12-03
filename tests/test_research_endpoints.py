"""Tests for research crawler endpoints."""
import json
import pytest
from unittest.mock import patch, MagicMock, AsyncMock
from fastapi.testclient import TestClient
from api.main import app

client = TestClient(app)

@pytest.fixture
def sample_research_request():
    """Sample research request data."""
    return {
        "query": "Infrastructure investment impact",
        "search_depth": 3,
        "max_pages": 10,
        "domains": ".gov,.edu",
        "report_type": "comprehensive",
        "language": "en",
        "include_images": False,
        "include_tables": True,
        "date_range": "1year"
    }

@pytest.fixture
def mock_db_connection():
    """Mock database connection."""
    with patch('psycopg2.connect') as mock_connect:
        mock_conn = MagicMock()
        mock_cur = MagicMock()
        mock_connect.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cur
        yield mock_cur

class TestResearchEndpoints:
    """Test cases for research crawler endpoints."""

    def test_start_research_success(self, sample_research_request):
        """Test successful research initiation."""
        response = client.post("/v1/research/start", json=sample_research_request)
        
        assert response.status_code == 200
        result = response.json()
        assert "task_id" in result
        assert result["status"] == "pending"
        assert result["message"] == "Research task started successfully"

    def test_start_research_validation_error(self):
        """Test research request with validation errors."""
        invalid_request = {
            "query": "",  # Empty query should fail
            "search_depth": 10,  # Too high
            "max_pages": 0  # Too low
        }
        
        response = client.post("/v1/research/start", json=invalid_request)
        assert response.status_code == 422  # Validation error

    def test_start_research_minimal_request(self):
        """Test research with minimal required fields."""
        minimal_request = {
            "query": "Test research query"
        }
        
        response = client.post("/v1/research/start", json=minimal_request)
        assert response.status_code == 200
        result = response.json()
        assert result["status"] == "pending"

    def test_get_research_status_not_found(self):
        """Test getting status for non-existent task."""
        fake_task_id = "non-existent-task-id"
        
        response = client.get(f"/v1/research/status/{fake_task_id}")
        assert response.status_code == 404
        assert response.json()["detail"] == "Task not found"

    def test_get_research_reports_empty(self, mock_db_connection):
        """Test getting reports when none exist."""
        mock_db_connection.fetchall.return_value = []
        
        response = client.get("/v1/research/reports")
        assert response.status_code == 200
        result = response.json()
        assert result == []

    def test_get_research_reports_with_data(self, mock_db_connection):
        """Test getting reports with sample data."""
        sample_report = {
            "id": "test-report-id",
            "title": "Test Report",
            "query": "Test query",
            "content": "This is test content for the report.",
            "metadata": {"test": "data"},
            "created_at": "2024-01-15T10:30:00",
            "status": "completed",
            "pages_crawled": 5,
            "sources": 5
        }
        
        mock_db_connection.fetchall.return_value = [sample_report]
        
        response = client.get("/v1/research/reports")
        assert response.status_code == 200
        result = response.json()
        assert len(result) == 1
        assert result[0]["id"] == "test-report-id"
        assert result[0]["title"] == "Test Report"

    def test_get_research_report_by_id(self, mock_db_connection):
        """Test getting a specific report by ID."""
        sample_report = {
            "id": "test-report-id",
            "title": "Test Report",
            "query": "Test query",
            "content": "This is test content for the report.",
            "metadata": {"test": "data"},
            "created_at": "2024-01-15T10:30:00",
            "status": "completed",
            "pages_crawled": 5,
            "sources": 5
        }
        
        mock_db_connection.fetchone.return_value = sample_report
        
        response = client.get("/v1/research/reports/test-report-id")
        assert response.status_code == 200
        result = response.json()
        assert result["id"] == "test-report-id"
        assert result["title"] == "Test Report"

    def test_get_research_report_not_found(self, mock_db_connection):
        """Test getting non-existent report."""
        mock_db_connection.fetchone.return_value = None
        
        response = client.get("/v1/research/reports/non-existent-id")
        assert response.status_code == 404
        assert response.json()["detail"] == "Report not found"

    def test_delete_research_report_success(self, mock_db_connection):
        """Test successful report deletion."""
        mock_db_connection.rowcount = 1  # Simulate successful deletion
        
        response = client.delete("/v1/research/reports/test-report-id")
        assert response.status_code == 200
        assert response.json()["message"] == "Report deleted successfully"

    def test_delete_research_report_not_found(self, mock_db_connection):
        """Test deleting non-existent report."""
        mock_db_connection.rowcount = 0  # Simulate no rows affected
        
        response = client.delete("/v1/research/reports/non-existent-id")
        assert response.status_code == 404
        assert response.json()["detail"] == "Report not found"


class TestWebCrawler:
    """Test cases for WebCrawler class."""

    @patch('aiohttp.ClientSession')
    async def test_crawler_initialization(self, mock_session):
        """Test crawler initialization."""
        from api.routes.research_endpoints import WebCrawler
        
        crawler = WebCrawler(max_pages=5, search_depth=2)
        assert crawler.max_pages == 5
        assert crawler.search_depth == 2
        assert len(crawler.crawled_pages) == 0
        assert len(crawler.visited_urls) == 0

    async def test_search_urls_basic(self):
        """Test URL search functionality."""
        from api.routes.research_endpoints import WebCrawler
        
        crawler = WebCrawler()
        urls = await crawler.search_urls("test query")
        
        assert isinstance(urls, list)
        assert len(urls) <= crawler.max_pages
        assert all(url.startswith('http') for url in urls)

    async def test_search_urls_with_domain_filter(self):
        """Test URL search with domain filtering."""
        from api.routes.research_endpoints import WebCrawler
        
        crawler = WebCrawler()
        urls = await crawler.search_urls("test query", domains=".gov")
        
        assert isinstance(urls, list)
        # All URLs should be from .gov domains
        assert all('.gov' in url for url in urls)

    @patch('aiohttp.ClientSession.get')
    async def test_crawl_page_success(self, mock_get):
        """Test successful page crawling."""
        from api.routes.research_endpoints import WebCrawler
        
        # Mock successful HTTP response
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.text = AsyncMock(return_value="<html><body>Test content</body></html>")
        mock_get.return_value.__aenter__.return_value = mock_response
        
        crawler = WebCrawler()
        session = MagicMock()
        
        result = await crawler.crawl_page(session, "https://example.com")
        
        assert result is not None
        assert result.url == "https://example.com"
        assert "Test content" in result.content or result.content


class TestReportGenerator:
    """Test cases for ReportGenerator class."""

    def test_generate_report_basic(self):
        """Test basic report generation."""
        from api.routes.research_endpoints import ReportGenerator, CrawledPage
        
        pages = [
            CrawledPage(
                url="https://example.com",
                title="Test Page",
                content="Test content",
                metadata={"word_count": 100}
            )
        ]
        
        report = ReportGenerator.generate_report("Test Query", pages, "comprehensive")
        
        assert "Test Query" in report
        assert "Research Report" in report
        assert "Executive Summary" in report
        assert "Methodology" in report
        assert "Key Findings" in report
        assert "https://example.com" in report

    def test_generate_report_empty_pages(self):
        """Test report generation with no pages."""
        from api.routes.research_endpoints import ReportGenerator
        
        report = ReportGenerator.generate_report("Empty Query", [], "summary")
        
        assert "Empty Query" in report
        assert "0 web pages" in report
        assert "Research Report" in report

    def test_generate_report_multiple_pages(self):
        """Test report generation with multiple pages."""
        from api.routes.research_endpoints import ReportGenerator, CrawledPage
        
        pages = [
            CrawledPage(
                url="https://example1.com",
                title="Page 1",
                content="Content 1",
                metadata={"word_count": 100}
            ),
            CrawledPage(
                url="https://example2.com",
                title="Page 2", 
                content="Content 2",
                metadata={"word_count": 150}
            )
        ]
        
        report = ReportGenerator.generate_report("Multi-page Query", pages, "detailed")
        
        assert "Multi-page Query" in report
        assert "2 web pages" in report
        assert "example1.com" in report
        assert "example2.com" in report
        assert "250 words" in report  # Total word count


if __name__ == "__main__":
    pytest.main([__file__])
