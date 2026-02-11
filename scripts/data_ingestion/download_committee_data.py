import os
import time

import requests

from config.committee_api_config import (
    COMMITTEE_BROWSE_URL,
    COMMITTEE_DATA_DIR,
    COMMITTEE_DETAILS_URL,
    COMMITTEE_DOCUMENTS_URL,
    HEADERS,
)


class CommitteeDataDownloader:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update(HEADERS)

    def get_all_committees(self):
        """Fetch list of all committees"""
        try:
            response = self.session.get(COMMITTEE_BROWSE_URL)
            response.raise_for_status()
            return response.json().get("committees", [])
        except requests.exceptions.RequestException as e:
            print(f"Error fetching committees: {e}")
            return []

    def get_committee_details(self, committee_id):
        """Fetch detailed information about a specific committee"""
        try:
            url = f"{COMMITTEE_DETAILS_URL}/{committee_id}"
            response = self.session.get(url)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"Error fetching committee {committee_id} details: {e}")
            return None

    def get_committee_documents(self, committee_id, start_date=None, end_date=None):
        """Fetch documents associated with a committee"""
        try:
            params = {"committee": committee_id}
            if start_date:
                params["startDate"] = start_date
            if end_date:
                params["endDate"] = end_date

            response = self.session.get(COMMITTEE_DOCUMENTS_URL, params=params)
            response.raise_for_status()
            return response.json().get("documents", [])
        except requests.exceptions.RequestException as e:
            print(f"Error fetching documents for committee {committee_id}: {e}")
            return []

    def save_data(self, data, file_name):
        """Save data to JSON file"""
        file_path = os.path.join(COMMITTEE_DATA_DIR, file_name)
        with open(file_path, "w") as f:
            json.dump(data, f, indent=2)
        print(f"Saved data to {file_path}")

    def download_all_committee_data(self):
        """Download data for all committees"""
        committees = self.get_all_committees()
        if not committees:
            print("No committees found")
            return

        for committee in committees:
            committee_id = committee.get("id")
            if not committee_id:
                continue

            print(f"Processing committee: {committee.get('name')}")

            # Get committee details
            details = self.get_committee_details(committee_id)
            if details:
                self.save_data(details, f"{committee_id}_details.json")

            # Get committee documents
            documents = self.get_committee_documents(committee_id)
            if documents:
                self.save_data(documents, f"{committee_id}_documents.json")

            # Rate limiting
            time.sleep(1)


if __name__ == "__main__":
    downloader = CommitteeDataDownloader()
    print("Starting committee data download...")
    downloader.download_all_committee_data()
    print("Committee data download complete!")
