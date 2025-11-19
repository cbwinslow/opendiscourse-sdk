import requests
from config.api_config import COLLECTIONS_URL, HEADERS


def get_collections():
    """Fetch available collections from GovInfo API"""
    try:
        response = requests.get(COLLECTIONS_URL, headers=HEADERS)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error fetching collections: {e}")
        return None


def display_collections(collections):
    """Display available collections in a readable format"""
    if not collections:
        print("No collections available")
        return

    print("Available GovInfo Collections:")
    print("-" * 40)
    for collection in collections["collections"]:
        print(f"Collection ID: {collection['collectionCode']}")
        print(f"Name: {collection['collectionName']}")
        print(f"Description: {collection.get('description', 'No description')}")
        print(f"Package Count: {collection.get('packageCount', 'Unknown')}")
        print(f"Last Modified: {collection.get('lastModified', 'Unknown')}")
        print("-" * 40)


if __name__ == "__main__":
    collections = get_collections()
    display_collections(collections)
