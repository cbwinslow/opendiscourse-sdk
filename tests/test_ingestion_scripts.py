import unittest
from unittest.mock import patch, MagicMock

import download_committee_data
import opendiscourse.services.scraping.govinfo_scraper as gov_scraper


class TestCommitteeDownloader(unittest.TestCase):
    def test_get_all_committees(self):
        downloader = download_committee_data.CommitteeDataDownloader()
        fake_response = MagicMock()
        fake_response.json.return_value = {
            "committees": [{"id": "A1", "name": "Alpha"}]
        }
        fake_response.raise_for_status.return_value = None
        with patch.object(
            downloader.session, "get", return_value=fake_response
        ) as mock_get:
            committees = downloader.get_all_committees()
            self.assertEqual(len(committees), 1)
            mock_get.assert_called_once_with(
                download_committee_data.COMMITTEE_BROWSE_URL
            )


class TestGovInfoScraper(unittest.TestCase):
    @patch("opendiscourse.services.scraping.govinfo_scraper.save_document")
    def test_fetch_metadata(self, mock_save):
        responses = []
        # collections list
        r1 = MagicMock()
        r1.json.return_value = {"collections": [{"collectionCode": "TEST"}]}
        r1.raise_for_status.return_value = None
        responses.append(r1)
        # documents list
        r2 = MagicMock()
        r2.json.return_value = {"packages": [{"packageId": "P1"}]}
        r2.raise_for_status.return_value = None
        responses.append(r2)
        # doc summary
        r3 = MagicMock()
        r3.json.return_value = {
            "title": "Doc",
            "dateIssued": "2020-01-01",
            "dateLastModified": "2020-01-02",
        }
        r3.raise_for_status.return_value = None
        responses.append(r3)
        # content xml
        r4 = MagicMock(status_code=200)
        r4.text = "<doc><section>Hi</section></doc>"
        responses.append(r4)
        with patch("requests.get", side_effect=responses):
            with patch(
                "opendiscourse.services.scraping.govinfo_scraper.get_db_connection"
            ):
                gov_scraper.fetch_govinfo_metadata()
        self.assertTrue(mock_save.called)


if __name__ == "__main__":
    unittest.main()
