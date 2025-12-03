#!/usr/bin/env python3
"""
RAG Database Script Orchestrator

This script provides orchestration and automation for all RAG database operations including:
- Automated processing pipelines
- Scheduled operations
- Script coordination and dependency management
- Monitoring and alerting
- Batch processing management
"""

import logging
import os
import sys
import subprocess
from typing import List, Dict, Any, Optional
from pathlib import Path
import json
import time
from datetime import datetime, timedelta
from concurrent.futures import ThreadPoolExecutor, as_completed
import schedule

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

try:
    import psycopg2
    from psycopg2.extras import RealDictCursor
    from dotenv import load_dotenv
except ImportError as e:
    print(f"Missing dependency: {e}")
    print("Please install required packages: pip install psycopg2-binary python-dotenv schedule")
    sys.exit(1)

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("rag_orchestrator.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()


class RAGOrchestrator:
    """Orchestrator for managing RAG database operations."""
    
    def __init__(self):
        """Initialize orchestrator."""
        self.scripts_dir = Path(__file__).parent
        self.db_connection = None
        self.processing_status = {}
        self._connect_to_database()
        logger.info("RAG Orchestrator initialized successfully")
    
    def _connect_to_database(self):
        """Establish database connection."""
        try:
            self.db_connection = psycopg2.connect(
                dbname=os.getenv("POSTGRES_DB", "opendiscourse"),
                user=os.getenv("POSTGRES_USER", "postgres"),
                password=os.getenv("POSTGRES_PASSWORD", "password"),
                host=os.getenv("POSTGRES_HOST", "localhost"),
                port=os.getenv("POSTGRES_PORT", "5432"),
            )
            logger.info("Database connection established")
        except Exception as e:
            logger.error(f"Failed to connect to database: {e}")
            raise
    
    def run_script(self, script_name: str, args: List[str] = None) -> Dict[str, Any]:
        """
        Run a specific script with given arguments.
        
        Args:
            script_name: Name of the script to run
            args: List of command line arguments
            
        Returns:
            Dictionary containing execution results
        """
        script_path = self.scripts_dir / script_name
        if not script_path.exists():
            raise FileNotFoundError(f"Script not found: {script_path}")
        
        command = [sys.executable, str(script_path)]
        if args:
            command.extend(args)
        
        logger.info(f"Running script: {' '.join(command)}")
        
        start_time = datetime.now()
        
        try:
            result = subprocess.run(
                command,
                capture_output=True,
                text=True,
                timeout=3600  # 1 hour timeout
            )
            
            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()
            
            execution_result = {
                'script': script_name,
                'args': args or [],
                'start_time': start_time.isoformat(),
                'end_time': end_time.isoformat(),
                'duration_seconds': duration,
                'return_code': result.returncode,
                'stdout': result.stdout,
                'stderr': result.stderr,
                'success': result.returncode == 0
            }
            
            if result.returncode == 0:
                logger.info(f"Script {script_name} completed successfully in {duration:.2f}s")
            else:
                logger.error(f"Script {script_name} failed with return code {result.returncode}")
                logger.error(f"Error output: {result.stderr}")
            
            return execution_result
            
        except subprocess.TimeoutExpired:
            logger.error(f"Script {script_name} timed out after 1 hour")
            return {
                'script': script_name,
                'args': args or [],
                'start_time': start_time.isoformat(),
                'end_time': datetime.now().isoformat(),
                'error': 'Timeout after 1 hour',
                'success': False
            }
        except Exception as e:
            logger.error(f"Error running script {script_name}: {e}")
            return {
                'script': script_name,
                'args': args or [],
                'start_time': start_time.isoformat(),
                'end_time': datetime.now().isoformat(),
                'error': str(e),
                'success': False
            }
    
    def process_new_documents(self) -> Dict[str, Any]:
        """
        Process new documents that haven't been analyzed yet.
        
        Returns:
            Dictionary containing processing results
        """
        logger.info("Starting new document processing pipeline")
        
        # Get list of unprocessed documents
        cursor = self.db_connection.cursor(cursor_factory=RealDictCursor)
        cursor.execute("""
            SELECT id FROM documents 
            WHERE NOT is_deleted 
            AND (content_vector IS NULL OR id NOT IN (
                SELECT DISTINCT document_id FROM document_entity_map
            ))
            ORDER BY created_at ASC
        """)
        
        unprocessed_docs = [row['id'] for row in cursor.fetchall()]
        cursor.close()
        
        if not unprocessed_docs:
            logger.info("No unprocessed documents found")
            return {
                'processed_documents': 0,
                'total_documents': 0,
                'processing_time': 0,
                'success': True
            }
        
        logger.info(f"Found {len(unprocessed_docs)} unprocessed documents")
        
        # Process documents in batches
        batch_size = 10
        processed_count = 0
        failed_count = 0
        start_time = datetime.now()
        
        for i in range(0, len(unprocessed_docs), batch_size):
            batch = unprocessed_docs[i:i + batch_size]
            
            # Use ThreadPoolExecutor for parallel processing
            with ThreadPoolExecutor(max_workers=min(5, len(batch))) as executor:
                futures = []
                
                for doc_id in batch:
                    future = executor.submit(
                        self.run_script,
                        'rag_nlp_operations.py',
                        ['--document-id', str(doc_id)]
                    )
                    futures.append((doc_id, future))
                
                # Wait for batch completion
                for doc_id, future in futures:
                    try:
                        result = future.result(timeout=600)  # 10 minute timeout per document
                        if result['success']:
                            processed_count += 1
                            logger.info(f"Successfully processed document {doc_id}")
                        else:
                            failed_count += 1
                            logger.error(f"Failed to process document {doc_id}")
                    except Exception as e:
                        failed_count += 1
                        logger.error(f"Error processing document {doc_id}: {e}")
            
            # Brief pause between batches
            time.sleep(1)
        
        end_time = datetime.now()
        total_time = (end_time - start_time).total_seconds()
        
        result = {
            'total_documents': len(unprocessed_docs),
            'processed_documents': processed_count,
            'failed_documents': failed_count,
            'processing_time': total_time,
            'start_time': start_time.isoformat(),
            'end_time': end_time.isoformat(),
            'success': failed_count == 0
        }
        
        logger.info(f"Document processing completed: {processed_count} processed, {failed_count} failed")
        return result
    
    def run_data_validation(self) -> Dict[str, Any]:
        """
        Run comprehensive data validation.
        
        Returns:
            Dictionary containing validation results
        """
        logger.info("Running data validation pipeline")
        
        validation_result = self.run_script('rag_data_management.py', ['--validate'])
        
        if validation_result['success']:
            # Parse validation output to get structured results
            try:
                # Extract JSON from stdout
                stdout = validation_result['stdout']
                # Find JSON content in the output
                json_start = stdout.find('{')
                if json_start != -1:
                    json_content = stdout[json_start:]
                    validation_data = json.loads(json_content)
                    validation_result['validation_data'] = validation_data
            except json.JSONDecodeError:
                logger.warning("Could not parse validation output as JSON")
        
        return validation_result
    
    def run_maintenance_tasks(self) -> Dict[str, Any]:
        """
        Run routine maintenance tasks.
        
        Returns:
            Dictionary containing maintenance results
        """
        logger.info("Running maintenance tasks")
        
        maintenance_results = {
            'start_time': datetime.now().isoformat(),
            'tasks': {},
            'overall_success': True
        }
        
        # Task 1: Data validation
        logger.info("Running data validation...")
        validation_result = self.run_script('rag_data_management.py', ['--validate'])
        maintenance_results['tasks']['data_validation'] = validation_result
        if not validation_result['success']:
            maintenance_results['overall_success'] = False
        
        # Task 2: Duplicate detection
        logger.info("Running duplicate detection...")
        duplicate_result = self.run_script('rag_data_management.py', ['--detect-duplicates'])
        maintenance_results['tasks']['duplicate_detection'] = duplicate_result
        if not duplicate_result['success']:
            maintenance_results['overall_success'] = False
        
        # Task 3: Data cleaning (dry run)
        logger.info("Running data cleaning (dry run)...")
        cleaning_result = self.run_script('rag_data_management.py', ['--clean', '--dry-run'])
        maintenance_results['tasks']['data_cleaning'] = cleaning_result
        if not cleaning_result['success']:
            maintenance_results['overall_success'] = False
        
        # Task 4: Performance report
        logger.info("Generating performance report...")
        performance_result = self.run_script('rag_query_reporting.py', ['--performance-report'])
        maintenance_results['tasks']['performance_report'] = performance_result
        if not performance_result['success']:
            maintenance_results['overall_success'] = False
        
        maintenance_results['end_time'] = datetime.now().isoformat()
        
        logger.info(f"Maintenance tasks completed. Overall success: {maintenance_results['overall_success']}")
        return maintenance_results
    
    def generate_daily_report(self) -> Dict[str, Any]:
        """
        Generate daily activity and insights report.
        
        Returns:
            Dictionary containing daily report
        """
        logger.info("Generating daily report")
        
        report = {
            'report_date': datetime.now().date().isoformat(),
            'generated_at': datetime.now().isoformat(),
            'sections': {}
        }
        
        # Get content insights for last 24 hours
        insights_result = self.run_script('rag_query_reporting.py', ['--content-insights', '1'])
        if insights_result['success']:
            report['sections']['daily_insights'] = insights_result['stdout']
        
        # Get database analytics
        analytics_result = self.run_script('rag_query_reporting.py', ['--document-analytics'])
        if analytics_result['success']:
            report['sections']['database_analytics'] = analytics_result['stdout']
        
        # Get top entities from today
        entity_result = self.run_script('rag_query_reporting.py', ['--entity-search', '', '--limit', '20'])
        if entity_result['success']:
            report['sections']['top_entities'] = entity_result['stdout']
        
        return report
    
    def run_scheduled_tasks(self):
        """Set up and run scheduled tasks."""
        logger.info("Setting up scheduled tasks")
        
        # Schedule daily document processing
        schedule.every().day.at("02:00").do(self.process_new_documents)
        
        # Schedule weekly maintenance
        schedule.every().sunday.at("03:00").do(self.run_maintenance_tasks)
        
        # Schedule daily reports
        schedule.every().day.at("08:00").do(self.generate_daily_report)
        
        # Schedule validation every 6 hours
        schedule.every(6).hours.do(self.run_data_validation)
        
        logger.info("Scheduled tasks configured. Starting scheduler...")
        
        while True:
            schedule.run_pending()
            time.sleep(60)  # Check every minute
    
    def run_full_pipeline(self) -> Dict[str, Any]:
        """
        Run the complete processing pipeline.
        
        Returns:
            Dictionary containing pipeline results
        """
        logger.info("Running full RAG processing pipeline")
        
        pipeline_start = datetime.now()
        pipeline_results = {
            'pipeline_start': pipeline_start.isoformat(),
            'stages': {},
            'overall_success': True
        }
        
        # Stage 1: Process new documents
        logger.info("Stage 1: Processing new documents")
        processing_result = self.process_new_documents()
        pipeline_results['stages']['document_processing'] = processing_result
        if not processing_result['success']:
            pipeline_results['overall_success'] = False
        
        # Stage 2: Data validation
        logger.info("Stage 2: Data validation")
        validation_result = self.run_data_validation()
        pipeline_results['stages']['data_validation'] = validation_result
        if not validation_result['success']:
            pipeline_results['overall_success'] = False
        
        # Stage 3: Quality assessment
        logger.info("Stage 3: Quality assessment")
        quality_result = self.run_script('rag_data_management.py', ['--quality-report'])
        pipeline_results['stages']['quality_assessment'] = quality_result
        if not quality_result['success']:
            pipeline_results['overall_success'] = False
        
        # Stage 4: Generate insights report
        logger.info("Stage 4: Generating insights")
        insights_result = self.run_script('rag_query_reporting.py', ['--content-insights', '7'])
        pipeline_results['stages']['insights_generation'] = insights_result
        if not insights_result['success']:
            pipeline_results['overall_success'] = False
        
        pipeline_end = datetime.now()
        pipeline_duration = (pipeline_end - pipeline_start).total_seconds()
        
        pipeline_results['pipeline_end'] = pipeline_end.isoformat()
        pipeline_results['total_duration'] = pipeline_duration
        
        logger.info(f"Full pipeline completed in {pipeline_duration:.2f}s. Success: {pipeline_results['overall_success']}")
        return pipeline_results
    
    def monitor_system_health(self) -> Dict[str, Any]:
        """
        Monitor system health and database status.
        
        Returns:
            Dictionary containing health metrics
        """
        health_status = {
            'timestamp': datetime.now().isoformat(),
            'database_status': 'unknown',
            'script_availability': {},
            'recent_errors': [],
            'recommendations': []
        }
        
        # Check database connectivity
        try:
            cursor = self.db_connection.cursor()
            cursor.execute("SELECT 1")
            cursor.close()
            health_status['database_status'] = 'healthy'
        except Exception as e:
            health_status['database_status'] = 'error'
            health_status['recent_errors'].append(f"Database connection error: {str(e)}")
        
        # Check script availability
        scripts = [
            'rag_nlp_operations.py',
            'rag_data_management.py',
            'rag_query_reporting.py'
        ]
        
        for script in scripts:
            script_path = self.scripts_dir / script
            health_status['script_availability'][script] = script_path.exists()
        
        # Check for recent processing errors
        log_file = Path("rag_orchestrator.log")
        if log_file.exists():
            try:
                with open(log_file, 'r') as f:
                    lines = f.readlines()[-100:]  # Last 100 lines
                    error_lines = [line for line in lines if 'ERROR' in line]
                    health_status['recent_errors'].extend(error_lines[-5:])  # Last 5 errors
            except Exception:
                pass
        
        # Generate recommendations
        if health_status['database_status'] != 'healthy':
            health_status['recommendations'].append("Check database connectivity and configuration")
        
        if any(not available for available in health_status['script_availability'].values()):
            health_status['recommendations'].append("Ensure all required scripts are available")
        
        if health_status['recent_errors']:
            health_status['recommendations'].append("Review recent errors and take corrective action")
        
        return health_status
    
    def close(self):
        """Close database connection."""
        if self.db_connection:
            self.db_connection.close()
            logger.info("Database connection closed")


def main():
    """Main execution function."""
    import argparse
    
    parser = argparse.ArgumentParser(description="RAG Database Script Orchestrator")
    parser.add_argument('--process-new', action='store_true', help='Process new documents')
    parser.add_argument('--validate', action='store_true', help='Run data validation')
    parser.add_argument('--maintenance', action='store_true', help='Run maintenance tasks')
    parser.add_argument('--daily-report', action='store_true', help='Generate daily report')
    parser.add_argument('--full-pipeline', action='store_true', help='Run full processing pipeline')
    parser.add_argument('--health-check', action='store_true', help='Check system health')
    parser.add_argument('--schedule', action='store_true', help='Run scheduled tasks (blocking)')
    parser.add_argument('--run-script', type=str, help='Run specific script')
    parser.add_argument('--script-args', nargs='*', help='Arguments for script')
    
    args = parser.parse_args()
    
    orchestrator = RAGOrchestrator()
    
    try:
        if args.process_new:
            result = orchestrator.process_new_documents()
            print(json.dumps(result, indent=2, default=str))
        
        elif args.validate:
            result = orchestrator.run_data_validation()
            print(json.dumps(result, indent=2, default=str))
        
        elif args.maintenance:
            result = orchestrator.run_maintenance_tasks()
            print(json.dumps(result, indent=2, default=str))
        
        elif args.daily_report:
            result = orchestrator.generate_daily_report()
            print(json.dumps(result, indent=2, default=str))
        
        elif args.full_pipeline:
            result = orchestrator.run_full_pipeline()
            print(json.dumps(result, indent=2, default=str))
        
        elif args.health_check:
            result = orchestrator.monitor_system_health()
            print(json.dumps(result, indent=2, default=str))
        
        elif args.schedule:
            orchestrator.run_scheduled_tasks()  # This blocks
        
        elif args.run_script:
            result = orchestrator.run_script(args.run_script, args.script_args or [])
            print(json.dumps(result, indent=2, default=str))
        
        else:
            print("Please specify an operation. Use --help for available options.")
    
    finally:
        orchestrator.close()


if __name__ == "__main__":
    main()