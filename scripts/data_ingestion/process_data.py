import os
import xml.etree.ElementTree as ET
import json
import pandas as pd
from datetime import datetime
from collections import defaultdict


class DataProcessor:
    def __init__(self, data_dir="data"):
        self.data_dir = data_dir
        self.processed_dir = os.path.join(data_dir, "processed")
        os.makedirs(self.processed_dir, exist_ok=True)

        # Register collection processors
        self.processors = {
            "BILLS": self.process_bill,
            "FR": self.process_federal_register,
            # Add more collection processors as needed
        }

    def process_collection(self, collection_code):
        """Process all XML files in a collection directory"""
        collection_dir = os.path.join(self.data_dir, collection_code)
        if not os.path.exists(collection_dir):
            raise FileNotFoundError(f"Collection directory not found: {collection_dir}")

        processor = self.processors.get(collection_code, self.process_generic)
        processed_data = []

        for xml_file in os.listdir(collection_dir):
            if xml_file.endswith(".xml"):
                file_path = os.path.join(collection_dir, xml_file)
                try:
                    result = processor(file_path)
                    if result:
                        processed_data.append(result)
                except Exception as e:
                    print(f"Error processing {xml_file}: {str(e)}")

        # Save processed data
        self.save_processed_data(collection_code, processed_data)
        return processed_data

    def process_bill(self, xml_file):
        """Process a congressional bill XML file"""
        tree = ET.parse(xml_file)
        root = tree.getroot()

        # Extract bill metadata
        bill = {
            "bill_id": root.findtext("billNumber"),
            "bill_type": root.findtext("billType"),
            "congress": root.findtext("congress"),
            "title": root.findtext("title"),
            "introduced_date": root.findtext("introducedDate"),
            "sponsor": root.findtext("sponsor/fullName"),
            "current_status": root.findtext("currentStatus/status"),
            "last_action_date": root.findtext("currentStatus/actionDate"),
            "subjects": [
                subj.text for subj in root.findall("subjects/legislativeSubjects/item")
            ],
            "text_versions": self._process_text_versions(
                root.findall("textVersions/item")
            ),
            "actions": self._process_actions(root.findall("actions/item")),
            "original_file": os.path.basename(xml_file),
            "processing_timestamp": datetime.now().isoformat(),
        }

        return bill

    def _process_text_versions(self, text_version_items):
        """Process text versions of a bill"""
        return [
            {
                "type": item.findtext("type"),
                "date": item.findtext("date"),
                "formats": [fmt.text for fmt in item.findall("formats/item")],
            }
            for item in text_version_items
        ]

    def _process_actions(self, action_items):
        """Process legislative actions"""
        return [
            {
                "action_date": item.findtext("actionDate"),
                "action_text": item.findtext("text"),
                "committee": item.findtext("committee/name"),
                "action_type": item.findtext("type"),
            }
            for item in action_items
        ]

    def process_federal_register(self, xml_file):
        """Process a Federal Register document XML file"""
        tree = ET.parse(xml_file)
        root = tree.getroot()

        document = {
            "document_number": root.findtext("documentNumber"),
            "publication_date": root.findtext("publicationDate"),
            "title": root.findtext("title"),
            "agency": root.findtext("agency"),
            "action": root.findtext("action"),
            "summary": root.findtext("summary"),
            "dates": root.findtext("dates"),
            "addresses": root.findtext("addresses"),
            "further_info": root.findtext("furtherInformation"),
            "supplementary_info": root.findtext("supplementaryInformation"),
            "signature": root.findtext("signature"),
            "cfr_parts": [part.text for part in root.findall("cfrPart")],
            "original_file": os.path.basename(xml_file),
            "processing_timestamp": datetime.now().isoformat(),
        }

        return document

    def process_generic(self, xml_file):
        """Generic XML processor for collections without specific handlers"""
        tree = ET.parse(xml_file)
        root = tree.getroot()

        # Flatten XML structure into key-value pairs
        data = {"original_file": os.path.basename(xml_file)}
        self._flatten_xml(root, data)
        return data

    def _flatten_xml(self, element, data, parent_key=""):
        """Recursively flatten XML structure"""
        for child in element:
            new_key = f"{parent_key}_{child.tag}" if parent_key else child.tag
            if len(child) == 0:  # Leaf node
                data[new_key] = child.text
            else:
                self._flatten_xml(child, data, new_key)

    def save_processed_data(self, collection_code, data):
        """Save processed data in multiple formats"""
        if not data:
            return

        # Create collection processed directory
        collection_processed_dir = os.path.join(self.processed_dir, collection_code)
        os.makedirs(collection_processed_dir, exist_ok=True)

        # Current timestamp for filenames
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        # Save as JSON
        json_file = os.path.join(
            collection_processed_dir, f"{collection_code}_{timestamp}.json"
        )
        with open(json_file, "w") as f:
            json.dump(data, f, indent=2)

        # Save as CSV (flatten nested structures)
        csv_file = os.path.join(
            collection_processed_dir, f"{collection_code}_{timestamp}.csv"
        )
        df = pd.json_normalize(data)
        df.to_csv(csv_file, index=False)

        # Save as Parquet for efficient storage
        parquet_file = os.path.join(
            collection_processed_dir, f"{collection_code}_{timestamp}.parquet"
        )
        df.to_parquet(parquet_file, index=False)

        print(
            f"Saved processed data for {collection_code} collection in multiple formats"
        )


if __name__ == "__main__":
    processor = DataProcessor()

    # Example usage - process BILLS and FR collections
    collections_to_process = ["BILLS", "FR"]

    for collection in collections_to_process:
        print(f"Processing {collection} collection...")
        processed_data = processor.process_collection(collection)
        print(f"Processed {len(processed_data)} documents from {collection} collection")
