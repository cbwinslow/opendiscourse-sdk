import os
import requests
import time
from datetime import datetime
from config.member_api_config import (
    MEMBER_LIST_URL,
    MEMBER_DETAILS_URL,
    HEADERS,
    MEMBER_DATA_DIR,
)


class MemberDataDownloader:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update(HEADERS)

    def get_all_members(self, congress=None):
        """Fetch list of all members for a specific Congress"""
        params = {}
        if congress:
            params["congress"] = congress

        try:
            response = self.session.get(MEMBER_LIST_URL, params=params)
            response.raise_for_status()
            return response.json().get("members", [])
        except requests.exceptions.RequestException as e:
            print(f"Error fetching members: {e}")
            return []

    def get_member_details(self, member_id):
        """Fetch detailed information about a specific member"""
        try:
            url = MEMBER_DETAILS_URL.format(member_id=member_id)
            response = self.session.get(url)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"Error fetching member {member_id} details: {e}")
            return None

    def save_member_data(self, data, file_name):
        """Save member data to JSON file"""
        file_path = os.path.join(MEMBER_DATA_DIR, file_name)
        with open(file_path, "w") as f:
            json.dump(data, f, indent=2)
        print(f"Saved member data to {file_path}")

    def download_historical_members(self, start_congress=94, end_congress=None):
        """Download member data for multiple Congress sessions"""
        if end_congress is None:
            end_congress = self.get_current_congress()

        for congress in range(start_congress, end_congress + 1):
            print(f"Processing Congress {congress}...")
            members = self.get_all_members(congress)
            if not members:
                continue

            for member in members:
                member_id = member.get("id")
                if not member_id:
                    continue

                # Get member details
                details = self.get_member_details(member_id)
                if details:
                    file_name = f"member_{member_id}_congress_{congress}.json"
                    self.save_member_data(details, file_name)

                # Rate limiting
                time.sleep(0.5)

    def get_current_congress(self):
        """Get the current Congress number based on the current year"""
        # Each Congress lasts 2 years, starting in odd-numbered years
        # The first Congress was in 1789
        current_year = datetime.now().year
        return ((current_year - 1789) // 2) + 1


if __name__ == "__main__":
    downloader = MemberDataDownloader()
    print("Starting member data download...")
    downloader.download_historical_members(start_congress=94)
    print("Member data download complete!")
