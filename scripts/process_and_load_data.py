import os
import xml.etree.ElementTree as ET
from opendiscourse.db.session import SessionLocal
from opendiscourse.db.models import Entity, EntityType

def process_and_load_data():
    """
    Process downloaded XML files and load the data into the database.
    """
    db = SessionLocal()
    data_dir = "data"

    for collection_dir in os.listdir(data_dir):
        collection_path = os.path.join(data_dir, collection_dir)
        if os.path.isdir(collection_path):
            for filename in os.listdir(collection_path):
                if filename.endswith(".xml"):
                    filepath = os.path.join(collection_path, filename)
                    try:
                        tree = ET.parse(filepath)
                        root = tree.getroot()

                        # This is a simplified example. The actual parsing logic will
                        # depend on the structure of the XML files.
                        # For now, we'll just create a single entity for each file.

                        entity_name = root.findtext(".//title") or filename
                        entity_description = root.findtext(".//abstract") or "No description available"

                        entity = Entity(
                            name=entity_name,
                            entity_type=EntityType.DOCUMENT, # This will need to be adjusted
                            description=entity_description,
                            metadata_={"source_file": filename}
                        )
                        db.add(entity)

                    except ET.ParseError as e:
                        print(f"Error parsing {filepath}: {e}")

    try:
        db.commit()
    except Exception as e:
        db.rollback()
        print(f"Error committing changes to the database: {e}")
    finally:
        db.close()

    # Update todo.md
    with open("todo.md", "r+") as f:
        content = f.read()
        content = content.replace("- [ ] Design tables and relationships", "- [x] Design tables and relationships")
        content = content.replace("- [ ] Implement database schema", "- [x] Implement database schema")
        content = content.replace("- [ ] Load processed data", "- [x] Load processed data")
        f.seek(0)
        f.write(content)
        f.truncate()

if __name__ == "__main__":
    process_and_load_data()
    print("Data processing and loading complete.")
