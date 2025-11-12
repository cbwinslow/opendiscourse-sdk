import os
import xml.etree.ElementTree as ET
from lxml import etree
import hashlib


def validate_xml_structure(xml_file, xsd_file=None):
    """
    Validate XML structure against an XSD schema if provided, or basic XML well-formedness
    :param xml_file: Path to XML file
    :param xsd_file: Optional path to XSD schema file
    :return: Tuple of (is_valid, validation_errors)
    """
    try:
        # First check if file exists and is not empty
        if not os.path.exists(xml_file) or os.path.getsize(xml_file) == 0:
            return False, ["File is empty or does not exist"]

        # Basic XML well-formedness check
        try:
            ET.parse(xml_file)
        except ET.ParseError as e:
            return False, [f"XML parsing error: {str(e)}"]

        # If XSD schema is provided, validate against it
        if xsd_file:
            try:
                xmlschema = etree.XMLSchema(file=xsd_file)
                xml_doc = etree.parse(xml_file)
                xmlschema.assertValid(xml_doc)
            except etree.XMLSchemaParseError as e:
                return False, [f"XSD schema error: {str(e)}"]
            except etree.DocumentInvalid as e:
                return False, [f"XML validation error: {str(e)}"]

        return True, []

    except Exception as e:
        return False, [f"Unexpected validation error: {str(e)}"]


def calculate_file_hash(file_path, algorithm="sha256"):
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


def validate_data_directory(data_dir, collection_code):
    """
    Validate all XML files in a directory for a specific collection
    :param data_dir: Root data directory
    :param collection_code: Collection code to validate
    :return: Dictionary of validation results
    """
    collection_dir = os.path.join(data_dir, collection_code)
    if not os.path.exists(collection_dir):
        return {"error": f"Directory {collection_dir} does not exist"}

    validation_results = {
        "collection": collection_code,
        "total_files": 0,
        "valid_files": 0,
        "invalid_files": 0,
        "file_details": [],
    }

    for xml_file in os.listdir(collection_dir):
        if xml_file.endswith(".xml"):
            file_path = os.path.join(collection_dir, xml_file)
            validation_results["total_files"] += 1

            is_valid, errors = validate_xml_structure(file_path)
            file_hash = calculate_file_hash(file_path)

            file_result = {
                "file_name": xml_file,
                "is_valid": is_valid,
                "errors": errors,
                "file_size": os.path.getsize(file_path),
                "file_hash": file_hash,
                "last_modified": os.path.getmtime(file_path),
            }

            validation_results["file_details"].append(file_result)

            if is_valid:
                validation_results["valid_files"] += 1
            else:
                validation_results["invalid_files"] += 1

    return validation_results


def generate_validation_report(validation_results, report_file):
    """
    Generate a human-readable validation report
    :param validation_results: Dictionary of validation results
    :param report_file: Path to save report
    """
    with open(report_file, "w") as f:
        f.write(f"Validation Report for {validation_results['collection']}\n")
        f.write("=" * 50 + "\n")
        f.write(f"Total files: {validation_results['total_files']}\n")
        f.write(f"Valid files: {validation_results['valid_files']}\n")
        f.write(f"Invalid files: {validation_results['invalid_files']}\n\n")

        f.write("File Details:\n")
        f.write("-" * 50 + "\n")

        for file_detail in validation_results["file_details"]:
            f.write(f"File: {file_detail['file_name']}\n")
            f.write(f"Status: {'VALID' if file_detail['is_valid'] else 'INVALID'}\n")
            f.write(f"Size: {file_detail['file_size']} bytes\n")
            f.write(f"SHA256: {file_detail['file_hash']}\n")

            if not file_detail["is_valid"]:
                f.write("Errors:\n")
                for error in file_detail["errors"]:
                    f.write(f"  - {error}\n")

            f.write("-" * 50 + "\n")


if __name__ == "__main__":
    # Example usage
    data_dir = "data"
    collection = "BILLS"  # Example collection
    report_file = f"validation_report_{collection}.txt"

    print(f"Validating {collection} collection...")
    results = validate_data_directory(data_dir, collection)

    print(f"Generating report at {report_file}")
    generate_validation_report(results, report_file)

    print("Validation complete!")
