import logging
import time
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
import numpy as np
from dataclasses import dataclass
import asyncio
import aiohttp

@dataclass
class HealthCheckResult:
    """Result of a health check operation."""
    status: str
    latency_ms: float
    error_message: Optional[str] = None
    details: Optional[Dict] = None
    timestamp: datetime = datetime.now()

class StoreHealthChecker:
    """Health checker for specific vector store types."""
    
    def __init__(self, store_type: str, connection_info: Dict):
        self.store_type = store_type
        self.connection_info = connection_info
        self.logger = logging.getLogger(f"health_checker.{store_type}")
        
    async def check_connection(self) -> HealthCheckResult:
        """Check basic connection to the store."""
        start_time = time.time()
        try:
            if self.store_type == "elasticsearch":
                return await self._check_elasticsearch()
            elif self.store_type == "chromadb":
                return await self._check_chromadb()
            elif self.store_type == "pinecone":
                return await self._check_pinecone()
            else:
                raise ValueError(f"Unsupported store type: {self.store_type}")
                
        except Exception as e:
            latency = (time.time() - start_time) * 1000
            return HealthCheckResult(
                status="unhealthy",
                latency_ms=latency,
                error_message=str(e)
            )
            
    async def _check_elasticsearch(self) -> HealthCheckResult:
        """Check Elasticsearch health."""
        start_time = time.time()
        async with aiohttp.ClientSession() as session:
            try:
                url = f"http://{self.connection_info['host']}:{self.connection_info['port']}/_cluster/health"
                async with session.get(url) as response:
                    latency = (time.time() - start_time) * 1000
                    if response.status == 200:
                        health_data = await response.json()
                        return HealthCheckResult(
                            status="healthy" if health_data["status"] in ["green", "yellow"] else "unhealthy",
                            latency_ms=latency,
                            details=health_data
                        )
                    else:
                        return HealthCheckResult(
                            status="unhealthy",
                            latency_ms=latency,
                            error_message=f"HTTP {response.status}"
                        )
            except Exception as e:
                latency = (time.time() - start_time) * 1000
                return HealthCheckResult(
                    status="unhealthy",
                    latency_ms=latency,
                    error_message=str(e)
                )
                
    async def _check_chromadb(self) -> HealthCheckResult:
        """Check ChromaDB health."""
        start_time = time.time()
        try:
            # ChromaDB doesn't have a built-in health check endpoint
            # We'll try to list collections as a health check
            url = f"http://{self.connection_info['host']}:{self.connection_info['port']}/api/v1/collections"
            async with aiohttp.ClientSession() as session:
                async with session.get(url) as response:
                    latency = (time.time() - start_time) * 1000
                    if response.status == 200:
                        return HealthCheckResult(
                            status="healthy",
                            latency_ms=latency
                        )
                    else:
                        return HealthCheckResult(
                            status="unhealthy",
                            latency_ms=latency,
                            error_message=f"HTTP {response.status}"
                        )
        except Exception as e:
            latency = (time.time() - start_time) * 1000
            return HealthCheckResult(
                status="unhealthy",
                latency_ms=latency,
                error_message=str(e)
            )
            
    async def _check_pinecone(self) -> HealthCheckResult:
        """Check Pinecone health."""
        start_time = time.time()
        try:
            headers = {
                "Api-Key": self.connection_info.get("api_key"),
                "Accept": "application/json"
            }
            url = f"https://api.pinecone.io/indexes"
            async with aiohttp.ClientSession(headers=headers) as session:
                async with session.get(url) as response:
                    latency = (time.time() - start_time) * 1000
                    if response.status == 200:
                        return HealthCheckResult(
                            status="healthy",
                            latency_ms=latency
                        )
                    else:
                        return HealthCheckResult(
                            status="unhealthy",
                            latency_ms=latency,
                            error_message=f"HTTP {response.status}"
                        )
        except Exception as e:
            latency = (time.time() - start_time) * 1000
            return HealthCheckResult(
                status="unhealthy",
                latency_ms=latency,
                error_message=str(e)
            )

class EnhancedHealthChecker:
    """Enhanced health checker with comprehensive diagnostics."""
    
    def __init__(self, config: Dict):
        self.config = config
        self.logger = logging.getLogger("enhanced_health_checker")
        self.store_checkers = self._initialize_store_checkers()
        
    def _initialize_store_checkers(self) -> Dict[str, StoreHealthChecker]:
        """Initialize health checkers for each configured store."""
        checkers = {}
        for store_name, store_config in self.config["stores"].items():
            checkers[store_name] = StoreHealthChecker(
                store_type=store_name,
                connection_info=store_config
            )
        return checkers
        
    async def check_all_stores(self) -> Dict[str, HealthCheckResult]:
        """Check health of all configured stores."""
        tasks = []
        for store_name, checker in self.store_checkers.items():
            tasks.append(self._check_store_with_retry(store_name, checker))
            
        results = await asyncio.gather(*tasks)
        return dict(results)
        
    async def _check_store_with_retry(
        self, store_name: str, checker: StoreHealthChecker
    ) -> Tuple[str, HealthCheckResult]:
        """Check store health with retry logic."""
        retries = self.config["health_check"]["retries"]
        delay = 1  # Start with 1 second delay
        
        for attempt in range(retries):
            result = await checker.check_connection()
            if result.status == "healthy":
                return store_name, result
                
            if attempt < retries - 1:
                self.logger.warning(
                    f"Health check failed for {store_name}, "
                    f"attempt {attempt + 1}/{retries}. Retrying in {delay}s..."
                )
                await asyncio.sleep(delay)
                delay *= 2  # Exponential backoff
                
        return store_name, result
        
    async def run_diagnostics(self) -> Dict:
        """Run comprehensive diagnostics on all stores."""
        diagnostics = {
            "timestamp": datetime.now().isoformat(),
            "stores": {},
            "overall_status": "healthy"
        }
        
        # Check all stores
        store_results = await self.check_all_stores()
        
        for store_name, result in store_results.items():
            store_diagnostics = {
                "status": result.status,
                "latency_ms": result.latency_ms,
                "last_check": result.timestamp.isoformat()
            }
            
            if result.error_message:
                store_diagnostics["error"] = result.error_message
                
            if result.details:
                store_diagnostics["details"] = result.details
                
            diagnostics["stores"][store_name] = store_diagnostics
            
            # Update overall status
            if result.status != "healthy":
                diagnostics["overall_status"] = "unhealthy"
                
        return diagnostics
        
    def get_health_metrics(self, store_results: Dict[str, HealthCheckResult]) -> Dict:
        """Calculate health metrics from check results."""
        metrics = {
            "healthy_stores": 0,
            "unhealthy_stores": 0,
            "total_stores": len(store_results),
            "average_latency_ms": 0,
            "max_latency_ms": 0
        }
        
        latencies = []
        for result in store_results.values():
            if result.status == "healthy":
                metrics["healthy_stores"] += 1
            else:
                metrics["unhealthy_stores"] += 1
                
            latencies.append(result.latency_ms)
            
        if latencies:
            metrics["average_latency_ms"] = np.mean(latencies)
            metrics["max_latency_ms"] = max(latencies)
            
        return metrics
