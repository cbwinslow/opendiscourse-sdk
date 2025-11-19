import os
import json
import hashlib
from datetime import datetime
from config.committee_api_config import COMMITTEE_DATA_DIR


class CommitteeDataValidator:
    def __init__(self):
        self.validation_results = {
            "total_files": 0,
            "valid_files": 0,
            "invalid_files": 0,
            "file_details": [],
        }

    def validate_json_structure(self, file_path, schema=None):
        """
        Validate JSON file structure and content
        :param file_path: Path to JSON file
        :param schema: Optional JSON schema for validation
        :return: Tuple of (is_valid, validation_errors)
        """
        try:
            # Check if file exists and is not empty
            if not os.path.exists(file_path) or os.path.getsize(file_path) == 0:
                return False, ["File is empty or does not exist"]

            # Load and validate JSON
            with open(file_path, "r") as f:
                try:
                    data = json.load(f)
                except json.JSONDecodeError as e:
                    return False, [f"JSON parsing error: {str(e)}"]

            # Basic validation for committee data
            if "committee" not in data and "documents" not in data:
                return False, ["Invalid committee data structure"]

            return True, []

        except Exception as e:
            return False, [f"Unexpected validation error: {str(e)}"]

    def calculate_file_hash(self, file_path, algorithm="sha256"):
        """
        Calculate file hash for integrity checking
        :param file_path: Path to file
        :param algorithm: Hash algorithm to use
        :return: Hex digest of file hash
        """
        hash_func = getattr(hashlib, algorithm)()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_func.update(chunk)
        return hash_func.hexdigest()

    def validate_committee_directory(self):
        """
        Validate all committee data files in the directory
        :return: Dictionary of validation results
        """
        if not os.path.exists(COMMITTEE_DATA_DIR):
            return {"error": f"Directory {COMMITTEE_DATA_DIR} does not exist"}

        for file_name in os.listdir(COMMITTEE_DATA_DIR):
            if file_name.endswith(".json"):
                file_path = os.path.join(COMMITTEE_DATA_DIR, file_name)
                self.validation_results["total_files"] += 1

                is_valid, errors = self.validate_json_structure(file_path)
                file_hash = self.calculate_file_hash(file_path)

                file_result = {
                    "file_name": file_name,
                    "is_valid": is_valid,
                    "errors": errors,
                    "file_size": os.path.getsize(file_path),
                    "file_hash": file_hash,
                    "last_modified": os.path.getmtime(file_path),
                }

                self.validation_results["file_details"].append(file_result)

                if is_valid:
                    self.validation_results["valid_files"] += 1
                else:
                    self.validation_results["invalid_files"] += 1

        return self.validation_results

    def generate_validation_report(self, report_file):
        """
        Generate a human-readable validation report
        :param validation_results: Dictionary of validation results
        :param report_file: Path to save report
        """
        with open(report_file, "w") as f:
            f.write("Committee Data Validation Report\n")
            f.write("=" * 50 + "\n")
            f.write(f"Total files: {self.validation_results['total_files']}\n")
            f.write(f"Valid files: {self.validation_results['valid_files']}\n")
            f.write(f"Invalid files: {self.validation_results['invalid_files']}\n\n")

            f.write("File Details:\n")
            f.write("-" * 50 + "\n")

            for file_detail in self.validation_results["file_details"]:
                f.write(f"File: {file_detail['file_name']}\n")
                f.write(
                    f"Status: {'VALID' if file_detail['is_valid'] else 'INVALID'}\n"
                )
                f.write(f"Size: {file_detail['file_size']} bytes\n")
                f.write(f"SHA256: {file_detail['file_hash']}\n")

                if not file_detail["is_valid"]:
                    f.write("Errors:\n")
                    for error in file_detail["errors"]:
                        f.write(f"  - {error}\n")

                f.write("-" * 50 + "\n")


if __name__ == "__main__":
    validator = CommitteeDataValidator()

    print("Validating committee data...")
    results = validator.validate_committee_directory()

    report_file = "committee_validation_report.txt"
    print(f"Generating report at {report_file}")
    validator.generate_validation_report(report_file)

    print("Validation complete!")
