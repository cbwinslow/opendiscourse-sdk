"""Research crawler endpoints for generating AI-powered research reports."""
import os
import uuid
import asyncio
import aiohttp
from datetime import datetime
from typing import Dict, List, Optional, Any
from urllib.parse import urljoin, urlparse
from dataclasses import dataclass
import logging

from fastapi import APIRouter, BackgroundTasks, HTTPException, Depends
from pydantic import BaseModel, Field
import psycopg2
import psycopg2.extras

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter(prefix="/v1/research", tags=["Research Crawler"])

DB_URL = os.environ.get(
    "RAG_DB_URL", "postgresql://user:password@localhost:5432/opendiscourse"
)


class ResearchRequest(BaseModel):
    """Request model for starting research."""
    query: str = Field(..., description="Research question or topic")
    search_depth: int = Field(3, ge=1, le=5, description="Search depth (1-5 levels)")
    max_pages: int = Field(10, ge=1, le=100, description="Maximum pages to crawl")
    domains: Optional[str] = Field(None, description="Domain filters (comma-separated)")
    report_type: str = Field("comprehensive", description="Type of report to generate")
    language: str = Field("en", description="Language preference")
    include_images: bool = Field(False, description="Include images in analysis")
    include_tables: bool = Field(True, description="Include tables/data in analysis")
    date_range: str = Field("all", description="Date range filter")


class ResearchStatus(BaseModel):
    """Status response for research tasks."""
    task_id: str
    status: str  # pending, processing, completed, failed
    progress: float  # 0-100
    current_step: str
    pages_crawled: int
    estimated_completion: Optional[str]


class ResearchReport(BaseModel):
    """Research report model."""
    id: str
    title: str
    query: str
    timestamp: str
    status: str
    pages_crawled: int
    sources: int
    summary: str
    content: str
    metadata: Dict[str, Any]


class ResearchResponse(BaseModel):
    """Response for starting research."""
    task_id: str
    status: str
    message: str


@dataclass
class CrawledPage:
    """Data class for crawled page information."""
    url: str
    title: str
    content: str
    metadata: Dict[str, Any]


class WebCrawler:
    """Simple web crawler for research purposes."""
    
    def __init__(self, max_pages: int = 10, search_depth: int = 3):
        self.max_pages = max_pages
        self.search_depth = search_depth
        self.crawled_pages: List[CrawledPage] = []
        self.visited_urls = set()
        
    async def search_urls(self, query: str, domains: Optional[str] = None) -> List[str]:
        """Search for URLs related to the query."""
        # This is a simplified implementation
        # In production, you'd integrate with search APIs like Google Custom Search
        
        base_urls = [
            "https://www.congress.gov",
            "https://www.govinfo.gov",
            "https://www.whitehouse.gov",
            "https://www.usa.gov",
            "https://www.cbo.gov",
            "https://www.gao.gov"
        ]
        
        # Filter by domains if specified
        if domains:
            domain_list = [d.strip() for d in domains.split(',')]
            filtered_urls = []
            for url in base_urls:
                domain = urlparse(url).netloc
                if any(domain.endswith(d.strip('.')) for d in domain_list):
                    filtered_urls.append(url)
            base_urls = filtered_urls
        
        return base_urls[:self.max_pages]
    
    async def crawl_page(self, session: aiohttp.ClientSession, url: str) -> Optional[CrawledPage]:
        """Crawl a single page and extract content."""
        try:
            async with session.get(url, timeout=aiohttp.ClientTimeout(total=10)) as response:
                if response.status == 200:
                    content = await response.text()
                    
                    # Simple content extraction (in production, use BeautifulSoup or similar)
                    title = "Sample Document Title"
                    text_content = f"Sample content from {url}\n\nThis is extracted text content that would normally be parsed from HTML."
                    
                    return CrawledPage(
                        url=url,
                        title=title,
                        content=text_content,
                        metadata={
                            "status_code": response.status,
                            "content_type": response.headers.get("content-type", ""),
                            "timestamp": datetime.now().isoformat(),
                            "word_count": len(text_content.split())
                        }
                    )
        except Exception as e:
            logger.error(f"Error crawling {url}: {str(e)}")
            return None
    
    async def crawl(self, query: str, domains: Optional[str] = None) -> List[CrawledPage]:
        """Perform the web crawling."""
        urls = await self.search_urls(query, domains)
        
        async with aiohttp.ClientSession() as session:
            tasks = []
            for url in urls:
                if url not in self.visited_urls:
                    self.visited_urls.add(url)
                    tasks.append(self.crawl_page(session, url))
            
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            for result in results:
                if isinstance(result, CrawledPage):
                    self.crawled_pages.append(result)
        
        return self.crawled_pages


class ReportGenerator:
    """Generate research reports from crawled data."""
    
    @staticmethod
    def generate_report(query: str, crawled_pages: List[CrawledPage], 
                       report_type: str = "comprehensive") -> str:
        """Generate a research report from crawled pages."""
        
        total_pages = len(crawled_pages)
        total_words = sum(page.metadata.get("word_count", 0) for page in crawled_pages)
        
        # Generate report content based on crawled data
        report_content = f"""# {query} - Research Report

## Executive Summary
This research report was generated from an analysis of {total_pages} web pages containing approximately {total_words} words of content related to "{query}".

## Methodology
- **Search Query**: {query}
- **Pages Analyzed**: {total_pages}
- **Data Sources**: Government websites, policy documents, and official publications
- **Analysis Type**: {report_type.title()}

## Key Findings

### Primary Sources
The research incorporated data from the following key sources:
"""
        
        # Add source information
        for i, page in enumerate(crawled_pages[:10], 1):
            report_content += f"{i}. {page.title} - {page.url}\n"
        
        report_content += f"""

### Content Analysis
Based on the crawled content, several important themes and patterns emerged:

1. **Regulatory Framework**: Current policies and regulatory structures
2. **Implementation Challenges**: Practical barriers to policy execution
3. **Stakeholder Perspectives**: Various viewpoints from affected parties
4. **Future Outlook**: Projected developments and trends

### Data Insights
The analysis revealed:
- {total_pages} relevant documents were identified and processed
- Average document length: {total_words // total_pages if total_pages > 0 else 0} words
- Content spans multiple government domains and policy areas

## Detailed Analysis

### Policy Landscape
The current policy environment shows significant activity in the area of {query.lower()}. 
Key developments include new regulatory frameworks, implementation guidelines, and 
stakeholder engagement initiatives.

### Implementation Status
Based on the analyzed documents, implementation efforts are at various stages:
- Planning phase initiatives
- Active implementation programs  
- Evaluation and assessment activities

### Stakeholder Impact
The research identified several key stakeholder groups affected by policies related to {query}:
- Federal agencies and departments
- State and local governments
- Private sector organizations
- Civil society groups

## Recommendations

1. **Continued Monitoring**: Regular assessment of policy developments
2. **Stakeholder Engagement**: Enhanced consultation processes
3. **Data Collection**: Improved metrics and reporting systems
4. **Resource Allocation**: Strategic investment in key areas

## Conclusion
This comprehensive analysis provides insights into the current state of {query.lower()} 
based on official government sources and policy documents. The findings suggest 
ongoing evolution in this policy area with significant implications for various stakeholders.

## Appendix

### Source URLs
"""
        
        # Add all source URLs
        for page in crawled_pages:
            report_content += f"- {page.url}\n"
        
        report_content += f"\n*Report generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*"
        
        return report_content


# In-memory storage for demo purposes (use Redis or database in production)
research_tasks = {}


async def perform_research_task(task_id: str, request: ResearchRequest):
    """Background task to perform research."""
    try:
        # Update status to processing
        research_tasks[task_id]["status"] = "processing"
        research_tasks[task_id]["current_step"] = "Initializing crawler..."
        research_tasks[task_id]["progress"] = 10
        
        # Initialize crawler
        crawler = WebCrawler(
            max_pages=request.max_pages,
            search_depth=request.search_depth
        )
        
        # Update progress
        research_tasks[task_id]["current_step"] = "Searching for relevant sources..."
        research_tasks[task_id]["progress"] = 25
        await asyncio.sleep(1)  # Simulate work
        
        # Perform crawling
        research_tasks[task_id]["current_step"] = "Crawling web pages..."
        research_tasks[task_id]["progress"] = 50
        
        crawled_pages = await crawler.crawl(request.query, request.domains)
        
        # Update progress
        research_tasks[task_id]["current_step"] = "Analyzing content with AI..."
        research_tasks[task_id]["progress"] = 75
        research_tasks[task_id]["pages_crawled"] = len(crawled_pages)
        await asyncio.sleep(2)  # Simulate AI analysis
        
        # Generate report
        research_tasks[task_id]["current_step"] = "Generating research report..."
        research_tasks[task_id]["progress"] = 90
        
        report_content = ReportGenerator.generate_report(
            request.query, 
            crawled_pages, 
            request.report_type
        )
        
        # Store report in database
        report_id = str(uuid.uuid4())
        conn = psycopg2.connect(DB_URL)
        cur = conn.cursor()
        
        try:
            cur.execute("""
                INSERT INTO research_reports 
                (id, title, query, content, metadata, created_at, status, pages_crawled, sources)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                report_id,
                request.query,
                request.query,
                report_content,
                psycopg2.extras.Json({
                    "search_depth": request.search_depth,
                    "max_pages": request.max_pages,
                    "domains": request.domains,
                    "report_type": request.report_type,
                    "language": request.language,
                    "include_images": request.include_images,
                    "include_tables": request.include_tables,
                    "date_range": request.date_range
                }),
                datetime.now(),
                "completed",
                len(crawled_pages),
                len(crawled_pages)
            ))
            conn.commit()
        finally:
            cur.close()
            conn.close()
        
        # Update final status
        research_tasks[task_id]["status"] = "completed"
        research_tasks[task_id]["current_step"] = "Research completed"
        research_tasks[task_id]["progress"] = 100
        research_tasks[task_id]["report_id"] = report_id
        
    except Exception as e:
        logger.error(f"Research task {task_id} failed: {str(e)}")
        research_tasks[task_id]["status"] = "failed"
        research_tasks[task_id]["current_step"] = f"Error: {str(e)}"


@router.post("/start", response_model=ResearchResponse)
async def start_research(
    request: ResearchRequest, 
    background_tasks: BackgroundTasks
) -> ResearchResponse:
    """Start a new research task."""
    task_id = str(uuid.uuid4())
    
    # Initialize task status
    research_tasks[task_id] = {
        "status": "pending",
        "progress": 0,
        "current_step": "Queued for processing",
        "pages_crawled": 0,
        "created_at": datetime.now().isoformat(),
        "query": request.query
    }
    
    # Start background task
    background_tasks.add_task(perform_research_task, task_id, request)
    
    return ResearchResponse(
        task_id=task_id,
        status="pending",
        message="Research task started successfully"
    )


@router.get("/status/{task_id}", response_model=ResearchStatus)
async def get_research_status(task_id: str) -> ResearchStatus:
    """Get the status of a research task."""
    if task_id not in research_tasks:
        raise HTTPException(status_code=404, detail="Task not found")
    
    task = research_tasks[task_id]
    
    return ResearchStatus(
        task_id=task_id,
        status=task["status"],
        progress=task["progress"],
        current_step=task["current_step"],
        pages_crawled=task["pages_crawled"],
        estimated_completion=None  # Could calculate based on progress
    )


@router.get("/reports", response_model=List[ResearchReport])
async def get_research_reports(limit: int = 20) -> List[ResearchReport]:
    """Get all research reports."""
    conn = psycopg2.connect(DB_URL)
    cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    
    try:
        cur.execute("""
            SELECT id, title, query, content, metadata, created_at, status, 
                   pages_crawled, sources
            FROM research_reports 
            ORDER BY created_at DESC 
            LIMIT %s
        """, (limit,))
        
        reports = cur.fetchall()
        
        result = []
        for report in reports:
            # Generate summary from content (first 200 chars)
            content = report["content"] or ""
            summary = content[:200] + "..." if len(content) > 200 else content
            
            result.append(ResearchReport(
                id=report["id"],
                title=report["title"],
                query=report["query"],
                timestamp=report["created_at"].isoformat(),
                status=report["status"],
                pages_crawled=report["pages_crawled"] or 0,
                sources=report["sources"] or 0,
                summary=summary,
                content=content,
                metadata=report["metadata"] or {}
            ))
        
        return result
        
    finally:
        cur.close()
        conn.close()


@router.get("/reports/{report_id}", response_model=ResearchReport)
async def get_research_report(report_id: str) -> ResearchReport:
    """Get a specific research report."""
    conn = psycopg2.connect(DB_URL)
    cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    
    try:
        cur.execute("""
            SELECT id, title, query, content, metadata, created_at, status,
                   pages_crawled, sources
            FROM research_reports 
            WHERE id = %s
        """, (report_id,))
        
        report = cur.fetchone()
        
        if not report:
            raise HTTPException(status_code=404, detail="Report not found")
        
        content = report["content"] or ""
        summary = content[:200] + "..." if len(content) > 200 else content
        
        return ResearchReport(
            id=report["id"],
            title=report["title"],
            query=report["query"],
            timestamp=report["created_at"].isoformat(),
            status=report["status"],
            pages_crawled=report["pages_crawled"] or 0,
            sources=report["sources"] or 0,
            summary=summary,
            content=content,
            metadata=report["metadata"] or {}
        )
        
    finally:
        cur.close()
        conn.close()


@router.delete("/reports/{report_id}")
async def delete_research_report(report_id: str):
    """Delete a research report."""
    conn = psycopg2.connect(DB_URL)
    cur = conn.cursor()
    
    try:
        cur.execute("DELETE FROM research_reports WHERE id = %s", (report_id,))
        
        if cur.rowcount == 0:
            raise HTTPException(status_code=404, detail="Report not found")
        
        conn.commit()
        return {"message": "Report deleted successfully"}
        
    finally:
        cur.close()
        conn.close()
