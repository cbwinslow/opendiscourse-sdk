import os
import time
from datetime import datetime, timedelta

import requests

from config.api_config import BASE_URL, HEADERS

# Directory setup
DATA_DIR = "data"
os.makedirs(DATA_DIR, exist_ok=True)


def download_collection(collection_code, start_date=None, end_date=None):
    """
    Download all packages from a specific collection
    :param collection_code: The collection code (e.g., 'BILLS')
    :param start_date: Start date in YYYY-MM-DD format (default: 30 days ago)
    :param end_date: End date in YYYY-MM-DD format (default: today)
    """
    # Set default dates if not provided
    if not end_date:
        end_date = datetime.now().strftime("%Y-%m-%d")
    if not start_date:
        start_date = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")

    # Create collection directory
    collection_dir = os.path.join(DATA_DIR, collection_code)
    os.makedirs(collection_dir, exist_ok=True)

    print(f"Downloading {collection_code} collection from {start_date} to {end_date}")

    # Get packages in the collection
    packages_url = f"{BASE_URL}/collections/{collection_code}/{start_date}/{end_date}"

    try:
        response = requests.get(packages_url, headers=HEADERS)
        response.raise_for_status()
        packages = response.json()

        # Download each package
        for package in packages["packages"]:
            package_id = package["packageId"]
            download_package(package_id, collection_dir)
            time.sleep(0.5)  # Rate limiting

    except requests.exceptions.RequestException as e:
        print(f"Error downloading collection {collection_code}: {e}")


def download_package(package_id, save_dir):
    """
    Download a single package
    :param package_id: The package ID to download
    :param save_dir: Directory to save the package
    """
    package_url = f"{BASE_URL}/packages/{package_id}/xml"
    save_path = os.path.join(save_dir, f"{package_id}.xml")

    if os.path.exists(save_path):
        print(f"Package {package_id} already exists, skipping")
        return

    try:
        response = requests.get(package_url, headers=HEADERS)
        response.raise_for_status()

        with open(save_path, "wb") as f:
            f.write(response.content)
        print(f"Downloaded package {package_id}")

    except requests.exceptions.RequestException as e:
        print(f"Error downloading package {package_id}: {e}")


if __name__ == "__main__":
    # Get available collections
    try:
        collections_url = f"{BASE_URL}/collections"
        response = requests.get(collections_url, headers=HEADERS)
        response.raise_for_status()
        available_collections = [c["collectionCode"] for c in response.json()["collections"]]
    except requests.exceptions.RequestException as e:
        print(f"Error getting collections: {e}")
        exit(1)

    # Prompt user to select collections
    print("Available collections:")
    for i, collection in enumerate(available_collections):
        print(f"{i+1}. {collection}")

    selected_indices = input("Enter the numbers of the collections to download (comma-separated): ")
    selected_collections = [available_collections[int(i)-1] for i in selected_indices.split(',')]

    # Download selected collections
    for collection in selected_collections:
        download_collection(collection)

    # Update todo.md
    with open("todo.md", "r+") as f:
        content = f.read()
        content = content.replace("- [ ] Identify target collections", "- [x] Identify target collections")
        content = content.replace("- [ ] Create download script", "- [x] Create download script")
        content = content.replace("- [ ] Set up storage structure", "- [x] Set up storage structure")
        f.seek(0)
        f.write(content)
        f.truncate()
