import json
import os
from datetime import datetime

import pandas as pd

from config.committee_api_config import COMMITTEE_DATA_DIR


class CommitteeDataProcessor:
    def __init__(self):
        self.processed_dir = os.path.join(COMMITTEE_DATA_DIR, "processed")
        os.makedirs(self.processed_dir, exist_ok=True)

    def process_all_committees(self):
        """Process all committee data files in the directory"""
        processed_data = []

        for file_name in os.listdir(COMMITTEE_DATA_DIR):
            if file_name.endswith("_details.json"):
                file_path = os.path.join(COMMITTEE_DATA_DIR, file_name)
                try:
                    committee_data = self.process_committee_file(file_path)
                    if committee_data:
                        processed_data.append(committee_data)
                except Exception as e:
                    print(f"Error processing {file_name}: {str(e)}")

        # Save processed data
        self.save_processed_data(processed_data)
        return processed_data

    def process_committee_file(self, file_path):
        """Process a single committee JSON file"""
        with open(file_path) as f:
            data = json.load(f)

        # Extract basic committee information
        committee = {
            "committee_id": data.get("committee", {}).get("id"),
            "name": data.get("committee", {}).get("name"),
            "type": data.get("committee", {}).get("type"),
            "chamber": data.get("committee", {}).get("chamber"),
            "jurisdiction": data.get("committee", {}).get("jurisdiction"),
            "website": data.get("committee", {}).get("website"),
            "parent_committee": data.get("committee", {}).get("parentCommittee"),
            "subcommittees": self._process_subcommittees(
                data.get("committee", {}).get("subcommittees", [])
            ),
            "members": self._process_members(
                data.get("committee", {}).get("members", [])
            ),
            "original_file": os.path.basename(file_path),
            "processing_timestamp": datetime.now().isoformat(),
        }

        return committee

    def _process_subcommittees(self, subcommittees):
        """Process subcommittee information"""
        return [
            {"id": sub.get("id"), "name": sub.get("name"), "type": sub.get("type")}
            for sub in subcommittees
        ]

    def _process_members(self, members):
        """Process committee member information"""
        return [
            {
                "member_id": member.get("id"),
                "name": member.get("name"),
                "role": member.get("role"),
                "party": member.get("party"),
                "state": member.get("state"),
                "begin_date": member.get("beginDate"),
                "end_date": member.get("endDate"),
            }
            for member in members
        ]

    def save_processed_data(self, data):
        """Save processed data in multiple formats"""
        if not data:
            return

        # Current timestamp for filenames
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        # Save as JSON
        json_file = os.path.join(
            self.processed_dir, f"committees_processed_{timestamp}.json"
        )
        with open(json_file, "w") as f:
            json.dump(data, f, indent=2)

        # Save as CSV (flatten nested structures)
        csv_file = os.path.join(
            self.processed_dir, f"committees_processed_{timestamp}.csv"
        )
        df = pd.json_normalize(data)
        df.to_csv(csv_file, index=False)

        # Save as Parquet for efficient storage
        parquet_file = os.path.join(
            self.processed_dir, f"committees_processed_{timestamp}.parquet"
        )
        df.to_parquet(parquet_file, index=False)

        print("Saved processed committee data in multiple formats")


if __name__ == "__main__":
    processor = CommitteeDataProcessor()
    print("Processing committee data...")
    processed_data = processor.process_all_committees()
    print(f"Successfully processed {len(processed_data)} committees")
