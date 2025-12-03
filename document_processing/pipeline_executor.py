from typing import List, Dict, Any, Optional
from dataclasses import dataclass
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
from tqdm import tqdm
import time
from datetime import datetime

from .document_ingestor import DocumentIngestor, ProcessedDocument

@dataclass
class ProcessingError:
    """Represents an error that occurred during document processing"""
    document_id: str
    error_type: str
    error_message: str
    timestamp: str
    step: str

@dataclass
class ProcessingProgress:
    """Tracks progress of document processing"""
    total_documents: int
    completed: int
    failed: int
    current_step: str
    start_time: datetime
    end_time: Optional[datetime] = None
    
    @property
    def duration(self) -> float:
        """Calculate processing duration in seconds"""
        if self.end_time:
            return (self.end_time - self.start_time).total_seconds()
        return (datetime.now() - self.start_time).total_seconds()
    
    @property
    def success_rate(self) -> float:
        """Calculate success rate as percentage"""
        if self.total_documents == 0:
            return 0.0
        return (self.completed / self.total_documents) * 100

@dataclass
class ProcessingResults:
    """Contains results and metadata from document processing pipeline"""
    processed_documents: List[ProcessedDocument]
    errors: List[ProcessingError]
    progress: ProcessingProgress
    metadata: Dict[str, Any]

class PipelineExecutor:
    """Handles execution of document processing pipeline with progress tracking and error handling"""
    
    def __init__(self, max_workers: int = 4):
        self.ingestor = DocumentIngestor()
        self.max_workers = max_workers
        self.logger = logging.getLogger(__name__)
        
    def _process_single_document(self, document: 'Document', 
                               progress: ProcessingProgress) -> tuple[ProcessedDocument, Optional[ProcessingError]]:
        """Process a single document and track errors"""
        error = None
        processed_doc = None
        
        try:
            # Update progress
            progress.current_step = f"Processing document {document.id}"
            
            # Process document
            processed_doc = self.ingestor.ingest(document)
            
            if processed_doc.error:  # Check for processing error
                error = ProcessingError(
                    document_id=document.id,
                    error_type="ProcessingError",
                    error_message=processed_doc.error,
                    timestamp=datetime.now().isoformat(),
                    step=progress.current_step
                )
                progress.failed += 1
            else:
                progress.completed += 1
                
        except Exception as e:
            error = ProcessingError(
                document_id=document.id,
                error_type=type(e).__name__,
                error_message=str(e),
                timestamp=datetime.now().isoformat(),
                step=progress.current_step
            )
            progress.failed += 1
            self.logger.error(f"Error processing document {document.id}: {str(e)}")
            
        return processed_doc, error

    def execute(self, documents: List['Document']) -> ProcessingResults:
        """Execute the processing pipeline on a list of documents"""
        # Initialize progress tracking
        progress = ProcessingProgress(
            total_documents=len(documents),
            completed=0,
            failed=0,
            current_step="Initializing",
            start_time=datetime.now()
        )
        
        processed_documents = []
        errors = []
        
        try:
            # Create progress bar
            pbar = tqdm(total=len(documents), desc="Processing documents")
            
            # Process documents in parallel
            with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
                # Submit all documents for processing
                future_to_doc = {
                    executor.submit(self._process_single_document, doc, progress): doc 
                    for doc in documents
                }
                
                # Process completed futures as they finish
                for future in as_completed(future_to_doc):
                    doc = future_to_doc[future]
                    
                    try:
                        processed_doc, error = future.result()
                        
                        if processed_doc:
                            processed_documents.append(processed_doc)
                        if error:
                            errors.append(error)
                            
                        # Update progress bar
                        pbar.update(1)
                        
                    except Exception as e:
                        # Handle unexpected errors
                        error = ProcessingError(
                            document_id=doc.id,
                            error_type="UnexpectedError",
                            error_message=str(e),
                            timestamp=datetime.now().isoformat(),
                            step=progress.current_step
                        )
                        errors.append(error)
                        progress.failed += 1
                        self.logger.error(f"Unexpected error processing document {doc.id}: {str(e)}")
                        
                        # Update progress bar
                        pbar.update(1)
            
            pbar.close()
            
        except Exception as e:
            self.logger.error(f"Pipeline execution error: {str(e)}")
            # Add pipeline-level error
            errors.append(ProcessingError(
                document_id="pipeline",
                error_type="PipelineError",
                error_message=str(e),
                timestamp=datetime.now().isoformat(),
                step=progress.current_step
            ))
        
        finally:
            # Finalize progress
            progress.end_time = datetime.now()
            progress.current_step = "Completed"
            
            # Compile results metadata
            metadata = {
                "start_time": progress.start_time.isoformat(),
                "end_time": progress.end_time.isoformat(),
                "duration_seconds": progress.duration,
                "success_rate": progress.success_rate,
                "total_documents": progress.total_documents,
                "completed_documents": progress.completed,
                "failed_documents": progress.failed,
                "max_workers": self.max_workers
            }
            
            return ProcessingResults(
                processed_documents=processed_documents,
                errors=errors,
                progress=progress,
                metadata=metadata
            )
            
    def get_processing_stats(self, results: ProcessingResults) -> Dict[str, Any]:
        """Generate detailed processing statistics from results"""
        stats = {
            "execution_time": results.progress.duration,
            "success_rate": results.progress.success_rate,
            "total_processed": len(results.processed_documents),
            "total_errors": len(results.errors),
            "error_types": {},
            "avg_document_size": 0,
            "total_entities": 0
        }
        
        # Analyze errors
        for error in results.errors:
            if error.error_type not in stats["error_types"]:
                stats["error_types"][error.error_type] = 0
            stats["error_types"][error.error_type] += 1
        
        # Analyze processed documents
        total_size = 0
        total_entities = 0
        
        for doc in results.processed_documents:
            if doc.content:
                total_size += len(doc.content)
            if doc.entities:
                total_entities += sum(len(entities) for entities in doc.entities.values())
        
        if results.processed_documents:
            stats["avg_document_size"] = total_size / len(results.processed_documents)
            stats["avg_entities_per_doc"] = total_entities / len(results.processed_documents)
        
        return stats
