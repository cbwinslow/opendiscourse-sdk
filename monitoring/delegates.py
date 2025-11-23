"""
Delegate functions for different data sources and table combinations.
"""

from typing import Dict, Any
from monitoring.progress_monitor import IngestionContext


def congress_members_delegate(context: IngestionContext, update_data: Dict[str, Any]):
    """Delegate for Congress members ingestion into congress.members table"""
    if update_data['success']:
        congress_num = context.metadata.get('congress', 'Unknown')
        processed = update_data['processed_count']
        throughput = processed / max(update_data['elapsed_time'] / 60, 0.01)

        print(f"📄 Congress {congress_num}: Processed member {context.current_record_id}")
        print(f"   Table: {context.table_name} | Members: {processed} | Throughput: {throughput:.1f}/min")

        # Track congress-specific progress
        if 'congress_members' not in context.metadata:
            context.metadata['congress_members'] = {}
        context.metadata['congress_members'][str(congress_num)] = processed

    else:
        error_type = update_data.get('error_details', {}).get('error_type', 'unknown')
        print(f"❌ Failed member {context.current_record_id}: {error_type}")


def congress_member_terms_delegate(context: IngestionContext, update_data: Dict[str, Any]):
    """Delegate for Congress member terms ingestion"""
    if update_data['success']:
        congress_num = context.metadata.get('congress', 'Unknown')
        terms_count = update_data['processed_count']

        print(f"🏛️ Congress {congress_num}: Processed {terms_count} member terms")

        # Track terms progress
        if 'member_terms' not in context.metadata:
            context.metadata['member_terms'] = {}
        context.metadata['member_terms'][str(congress_num)] = terms_count


def govinfo_documents_delegate(context: IngestionContext, update_data: Dict[str, Any]):
    """Delegate for GovInfo documents ingestion"""
    if update_data['success']:
        collection = context.metadata.get('collection', 'UNKNOWN')
        processed = update_data['processed_count']
        throughput = processed / max(update_data['elapsed_time'] / 60, 0.01)

        print(f"📑 GovInfo {collection}: Processed document {context.current_record_id}")
        print(f"   Table: {context.table_name} | Documents: {processed} | Throughput: {throughput:.1f}/min")


def entities_ingestion_delegate(context: IngestionContext, update_data: Dict[str, Any]):
    """Delegate for entity ingestion"""
    if update_data['success']:
        entity_type = context.metadata.get('entity_type', 'unknown')
        processed = update_data['processed_count']

        print(f"👤 Ingested {entity_type} entity: {context.current_record_id} (Total: {processed})")


def tasks_ingestion_delegate(context: IngestionContext, update_data: Dict[str, Any]):
    """Delegate for task ingestion"""
    if update_data['success']:
        task_type = context.metadata.get('task_type', 'unknown')
        processed = update_data['processed_count']

        print(f"✅ Created {task_type} task: {context.current_record_id} (Total: {processed})")


def setup_all_delegates(monitor):
    """Register all delegate functions"""
    # Congress data
    monitor.register_delegate("congress.gov", "congress.members", congress_members_delegate)
    monitor.register_delegate("congress.gov", "congress.member_terms", congress_member_terms_delegate)

    # GovInfo data
    monitor.register_delegate("govinfo.gov", "documents", govinfo_documents_delegate)

    # Generic entities and tasks
    monitor.register_delegate("various", "entities", entities_ingestion_delegate)
    monitor.register_delegate("various", "tasks", tasks_ingestion_delegate)

    return monitor
