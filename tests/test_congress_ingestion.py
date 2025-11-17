"""Tests for bulk data ingestion from Congress.gov and GovInfo APIs."""

import sys
import unittest
from unittest.mock import MagicMock, patch, Mock
from datetime import datetime

# Mock the dependencies before importing
sys.modules['vector_store'] = MagicMock()
sys.modules['vector_store.weaviate_manager'] = MagicMock()

import congress_api_ingest


class TestBulkDataIngester(unittest.TestCase):
    """Test cases for BulkDataIngester class."""

    def setUp(self):
        """Set up test fixtures."""
        self.govinfo_api_key = "test_govinfo_key"
        self.congress_api_key = "test_congress_key"

    @patch.dict("os.environ", {"GOVINFO_API_KEY": "test_key", "CONGRESS_API_KEY": "test_key"})
    def test_initialization(self):
        """Test ingester initialization."""
        ingester = congress_api_ingest.BulkDataIngester()
        self.assertIsNotNone(ingester)
        self.assertEqual(ingester.govinfo_api_key, "test_key")
        self.assertEqual(ingester.congress_api_key, "test_key")
        self.assertEqual(ingester.stats["total_documents"], 0)
        self.assertEqual(ingester.stats["successful_ingestions"], 0)

    def test_initialization_with_params(self):
        """Test ingester initialization with parameters."""
        ingester = congress_api_ingest.BulkDataIngester(
            govinfo_api_key=self.govinfo_api_key,
            congress_api_key=self.congress_api_key,
            data_dir="/tmp/test_data"
        )
        self.assertEqual(ingester.govinfo_api_key, self.govinfo_api_key)
        self.assertEqual(ingester.congress_api_key, self.congress_api_key)
        self.assertTrue(ingester.data_dir.exists())

    def test_create_session(self):
        """Test session creation with retry logic."""
        ingester = congress_api_ingest.BulkDataIngester(
            govinfo_api_key=self.govinfo_api_key,
            congress_api_key=self.congress_api_key
        )
        session = ingester._create_session()
        self.assertIsNotNone(session)
        # Check that adapters are mounted
        self.assertIn("http://", session.adapters)
        self.assertIn("https://", session.adapters)

    @patch("congress_api_ingest.BulkDataIngester._ingest_govinfo_package")
    @patch("requests.Session.get")
    def test_ingest_govinfo_collection_no_api_key(self, mock_get, mock_ingest):
        """Test GovInfo collection ingestion without API key."""
        ingester = congress_api_ingest.BulkDataIngester(
            govinfo_api_key=None,
            congress_api_key=self.congress_api_key
        )
        result = ingester.ingest_govinfo_collection("BILLS")
        self.assertEqual(result["total_documents"], 0)
        mock_get.assert_not_called()
        mock_ingest.assert_not_called()

    @patch("congress_api_ingest.BulkDataIngester._ingest_govinfo_package")
    @patch("requests.Session.get")
    def test_ingest_govinfo_collection_success(self, mock_get, mock_ingest):
        """Test successful GovInfo collection ingestion."""
        # Mock API response
        mock_response = MagicMock()
        mock_response.raise_for_status.return_value = None
        mock_response.json.return_value = {
            "packages": [
                {"packageId": "BILLS-118hr1"},
                {"packageId": "BILLS-118hr2"}
            ]
        }
        mock_get.return_value = mock_response
        mock_ingest.return_value = True

        ingester = congress_api_ingest.BulkDataIngester(
            govinfo_api_key=self.govinfo_api_key,
            congress_api_key=self.congress_api_key
        )

        result = ingester.ingest_govinfo_collection("BILLS", limit=2)

        # Verify API was called correctly
        mock_get.assert_called_once()
        call_args = mock_get.call_args
        self.assertIn("BILLS", call_args[0][0])

        # Verify packages were processed
        self.assertEqual(mock_ingest.call_count, 2)

    @patch("congress_api_ingest._save_document")
    @patch("requests.Session.get")
    def test_ingest_govinfo_package_success(self, mock_get, mock_save):
        """Test successful ingestion of a single GovInfo package."""
        # Mock responses
        summary_response = MagicMock()
        summary_response.raise_for_status.return_value = None
        summary_response.json.return_value = {
            "title": "Test Bill",
            "dateIssued": "2024-01-01",
            "docClass": "bill"
        }

        content_response = MagicMock()
        content_response.status_code = 200
        content_response.text = "Bill content here"
        content_response.raise_for_status.return_value = None

        mock_get.side_effect = [summary_response, content_response]
        mock_save.return_value = 123

        ingester = congress_api_ingest.BulkDataIngester(
            govinfo_api_key=self.govinfo_api_key,
            congress_api_key=self.congress_api_key
        )

        result = ingester._ingest_govinfo_package("TEST-PACKAGE", "BILLS")

        self.assertTrue(result)
        self.assertEqual(ingester.stats["total_documents"], 1)
        self.assertEqual(ingester.stats["successful_ingestions"], 1)
        mock_save.assert_called_once()

    @patch("congress_api_ingest._save_document")
    @patch("requests.Session.get")
    def test_ingest_govinfo_package_no_content(self, mock_get, mock_save):
        """Test ingestion when no content is available."""
        summary_response = MagicMock()
        summary_response.raise_for_status.return_value = None
        summary_response.json.return_value = {
            "title": "Test Bill",
            "dateIssued": "2024-01-01"
        }

        # All content format requests fail
        content_response = MagicMock()
        content_response.status_code = 404
        content_response.raise_for_status.side_effect = Exception("Not found")

        mock_get.side_effect = [summary_response] + [content_response] * 4

        ingester = congress_api_ingest.BulkDataIngester(
            govinfo_api_key=self.govinfo_api_key,
            congress_api_key=self.congress_api_key
        )

        result = ingester._ingest_govinfo_package("TEST-PACKAGE", "BILLS")

        self.assertFalse(result)
        self.assertEqual(ingester.stats["skipped_documents"], 1)
        mock_save.assert_not_called()

    @patch("congress_api_ingest.BulkDataIngester._ingest_congress_bill")
    @patch("requests.Session.get")
    def test_ingest_congress_bills_no_api_key(self, mock_get, mock_ingest):
        """Test Congress bills ingestion without API key."""
        ingester = congress_api_ingest.BulkDataIngester(
            govinfo_api_key=self.govinfo_api_key,
            congress_api_key=None
        )
        result = ingester.ingest_congress_bills(118)
        self.assertEqual(result["total_documents"], 0)
        mock_get.assert_not_called()
        mock_ingest.assert_not_called()

    @patch("congress_api_ingest.BulkDataIngester._ingest_congress_bill")
    @patch("requests.Session.get")
    def test_ingest_congress_bills_success(self, mock_get, mock_ingest):
        """Test successful Congress bills ingestion."""
        mock_response = MagicMock()
        mock_response.raise_for_status.return_value = None
        mock_response.json.return_value = {
            "bills": [
                {"number": 1, "type": "hr"},
                {"number": 2, "type": "hr"}
            ]
        }
        mock_get.return_value = mock_response
        mock_ingest.return_value = True

        ingester = congress_api_ingest.BulkDataIngester(
            govinfo_api_key=self.govinfo_api_key,
            congress_api_key=self.congress_api_key
        )

        result = ingester.ingest_congress_bills(118, bill_type="hr", limit=2)

        mock_get.assert_called_once()
        self.assertEqual(mock_ingest.call_count, 2)

    @patch("congress_api_ingest._save_document")
    @patch("requests.Session.get")
    def test_ingest_congress_bill_success(self, mock_get, mock_save):
        """Test successful ingestion of a single Congress bill."""
        bill_response = MagicMock()
        bill_response.raise_for_status.return_value = None
        bill_response.json.return_value = {
            "bill": {
                "title": "Test Bill",
                "url": "https://congress.gov/bill/118/hr/1",
                "introducedDate": "2024-01-01",
                "textVersions": {
                    "textVersions": [
                        {
                            "formats": [
                                {"url": "https://example.com/bill.txt"}
                            ]
                        }
                    ]
                }
            }
        }

        text_response = MagicMock()
        text_response.raise_for_status.return_value = None
        text_response.text = "Bill text content"

        mock_get.side_effect = [bill_response, text_response]
        mock_save.return_value = 456

        ingester = congress_api_ingest.BulkDataIngester(
            govinfo_api_key=self.govinfo_api_key,
            congress_api_key=self.congress_api_key
        )

        result = ingester._ingest_congress_bill(118, "hr", 1)

        self.assertTrue(result)
        self.assertEqual(ingester.stats["successful_ingestions"], 1)
        mock_save.assert_called_once()

    @patch("requests.Session.get")
    def test_ingest_congress_bill_no_text_versions(self, mock_get):
        """Test ingestion when bill has no text versions."""
        bill_response = MagicMock()
        bill_response.raise_for_status.return_value = None
        bill_response.json.return_value = {
            "bill": {
                "title": "Test Bill",
                "textVersions": {"textVersions": []}
            }
        }
        mock_get.return_value = bill_response

        ingester = congress_api_ingest.BulkDataIngester(
            govinfo_api_key=self.govinfo_api_key,
            congress_api_key=self.congress_api_key
        )

        result = ingester._ingest_congress_bill(118, "hr", 1)

        self.assertFalse(result)
        self.assertEqual(ingester.stats["skipped_documents"], 1)

    def test_fetch_package_content_xml_format(self):
        """Test fetching package content in XML format."""
        ingester = congress_api_ingest.BulkDataIngester(
            govinfo_api_key=self.govinfo_api_key,
            congress_api_key=self.congress_api_key
        )

        with patch("requests.Session.get") as mock_get:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.text = "<doc><title>Test</title></doc>"
            mock_response.raise_for_status.return_value = None
            mock_get.return_value = mock_response

            content = ingester._fetch_package_content("TEST-PACKAGE")

            self.assertIsNotNone(content)
            self.assertIn("Test", content)

    def test_fetch_package_content_no_formats_available(self):
        """Test fetching package content when no formats are available."""
        ingester = congress_api_ingest.BulkDataIngester(
            govinfo_api_key=self.govinfo_api_key,
            congress_api_key=self.congress_api_key
        )

        with patch("requests.Session.get") as mock_get:
            mock_response = MagicMock()
            mock_response.status_code = 404
            mock_response.raise_for_status.side_effect = Exception("Not found")
            mock_get.return_value = mock_response

            content = ingester._fetch_package_content("TEST-PACKAGE")

            self.assertIsNone(content)

    def test_print_statistics(self):
        """Test statistics printing."""
        ingester = congress_api_ingest.BulkDataIngester(
            govinfo_api_key=self.govinfo_api_key,
            congress_api_key=self.congress_api_key
        )
        ingester.stats["total_documents"] = 10
        ingester.stats["successful_ingestions"] = 8
        ingester.stats["failed_ingestions"] = 1
        ingester.stats["skipped_documents"] = 1

        # Should not raise any exception
        ingester.print_statistics()


if __name__ == "__main__":
    unittest.main()
