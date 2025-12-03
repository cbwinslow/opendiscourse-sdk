from typing import Dict, List, Optional
import time
from datetime import datetime, timedelta
import numpy as np
from dataclasses import dataclass
from prometheus_client import Counter, Histogram, Gauge, Summary
import psutil
import logging

@dataclass
class MetricDefinition:
    """Definition of a metric with its metadata."""
    name: str
    type: str
    description: str
    labels: List[str]
    buckets: Optional[List[float]] = None

class EnhancedMetricsCollector:
    """Enhanced metrics collection with detailed performance tracking."""
    
    def __init__(self):
        # Initialize metrics
        self._initialize_metrics()
        self.logger = logging.getLogger("enhanced_metrics")
        
    def _initialize_metrics(self):
        """Initialize all metric collectors."""
        # Operation Metrics
        self.search_latency = Histogram(
            "vector_store_search_latency_seconds",
            "Search operation latency in seconds",
            ["store", "query_type"],
            buckets=[.005, .01, .025, .05, .075, .1, .25, .5, .75, 1.0, 2.5, 5.0]
        )
        
        self.index_operations = Counter(
            "vector_store_index_operations_total",
            "Total number of index operations",
            ["store", "operation_type"]
        )
        
        self.query_count = Counter(
            "vector_store_queries_total",
            "Total number of queries",
            ["store", "query_type", "status"]
        )
        
        # Resource Metrics
        self.memory_usage = Gauge(
            "vector_store_memory_usage_bytes",
            "Memory usage in bytes",
            ["store"]
        )
        
        self.cpu_usage = Gauge(
            "vector_store_cpu_usage_percent",
            "CPU usage percentage",
            ["store"]
        )
        
        self.disk_usage = Gauge(
            "vector_store_disk_usage_bytes",
            "Disk usage in bytes",
            ["store", "type"]
        )
        
        # Performance Metrics
        self.query_throughput = Summary(
            "vector_store_query_throughput",
            "Queries per second",
            ["store"]
        )
        
        self.cache_hits = Counter(
            "vector_store_cache_hits_total",
            "Total number of cache hits",
            ["store", "cache_type"]
        )
        
        self.cache_misses = Counter(
            "vector_store_cache_misses_total",
            "Total number of cache misses",
            ["store", "cache_type"]
        )
        
        # Error Metrics
        self.errors = Counter(
            "vector_store_errors_total",
            "Total number of errors",
            ["store", "error_type"]
        )
        
        self.failed_operations = Counter(
            "vector_store_failed_operations_total",
            "Total number of failed operations",
            ["store", "operation_type"]
        )
        
    def record_search(self, store: str, query_type: str, duration: float, success: bool):
        """Record search operation metrics."""
        self.search_latency.labels(store=store, query_type=query_type).observe(duration)
        self.query_count.labels(
            store=store,
            query_type=query_type,
            status="success" if success else "failure"
        ).inc()
        
    def record_index_operation(self, store: str, operation_type: str):
        """Record index operation."""
        self.index_operations.labels(
            store=store,
            operation_type=operation_type
        ).inc()
        
    def update_resource_metrics(self, store: str):
        """Update resource usage metrics."""
        # Memory usage
        memory = psutil.virtual_memory()
        self.memory_usage.labels(store=store).set(memory.used)
        
        # CPU usage
        cpu_percent = psutil.cpu_percent()
        self.cpu_usage.labels(store=store).set(cpu_percent)
        
        # Disk usage
        disk = psutil.disk_usage('/')
        self.disk_usage.labels(store=store, type="used").set(disk.used)
        self.disk_usage.labels(store=store, type="free").set(disk.free)
        
    def record_cache_event(self, store: str, cache_type: str, hit: bool):
        """Record cache hit/miss."""
        if hit:
            self.cache_hits.labels(store=store, cache_type=cache_type).inc()
        else:
            self.cache_misses.labels(store=store, cache_type=cache_type).inc()
            
    def record_error(self, store: str, error_type: str):
        """Record error occurrence."""
        self.errors.labels(store=store, error_type=error_type).inc()
        
    def record_operation_failure(self, store: str, operation_type: str):
        """Record failed operation."""
        self.failed_operations.labels(
            store=store,
            operation_type=operation_type
        ).inc()

class PerformanceAnalyzer:
    """Analyze performance metrics and detect anomalies."""
    
    def __init__(self, window_size: int = 100):
        self.window_size = window_size
        self.latency_history: List[float] = []
        self.throughput_history: List[float] = []
        self.error_rate_history: List[float] = []
        
    def add_measurement(self, latency: float, throughput: float, error_rate: float):
        """Add new performance measurements."""
        self.latency_history.append(latency)
        self.throughput_history.append(throughput)
        self.error_rate_history.append(error_rate)
        
        # Keep only recent history
        if len(self.latency_history) > self.window_size:
            self.latency_history.pop(0)
            self.throughput_history.pop(0)
            self.error_rate_history.pop(0)
            
    def detect_anomalies(self) -> Dict[str, List[Dict]]:
        """Detect anomalies in performance metrics."""
        anomalies = {
            "latency": self._detect_metric_anomalies(self.latency_history, "latency"),
            "throughput": self._detect_metric_anomalies(self.throughput_history, "throughput"),
            "error_rate": self._detect_metric_anomalies(self.error_rate_history, "error_rate")
        }
        return anomalies
        
    def _detect_metric_anomalies(
        self, history: List[float], metric_name: str
    ) -> List[Dict]:
        """Detect anomalies in a specific metric."""
        if len(history) < self.window_size:
            return []
            
        anomalies = []
        mean = np.mean(history[:-1])  # Exclude current value
        std = np.std(history[:-1])
        current = history[-1]
        
        # Check if current value is an anomaly (> 3 standard deviations)
        if abs(current - mean) > 3 * std:
            anomalies.append({
                "metric": metric_name,
                "value": current,
                "mean": mean,
                "std": std,
                "timestamp": datetime.now().isoformat()
            })
            
        return anomalies

class MetricsAggregator:
    """Aggregate metrics across different stores and time periods."""
    
    def __init__(self):
        self.metrics_collector = EnhancedMetricsCollector()
        self.performance_analyzer = PerformanceAnalyzer()
        
    async def collect_metrics(self, store_names: List[str]) -> Dict:
        """Collect metrics from all stores."""
        metrics = {}
        
        for store in store_names:
            store_metrics = await self._collect_store_metrics(store)
            metrics[store] = store_metrics
            
            # Update performance analyzer
            self.performance_analyzer.add_measurement(
                latency=store_metrics["latency"]["avg"],
                throughput=store_metrics["throughput"]["current"],
                error_rate=store_metrics["error_rate"]
            )
            
        # Check for anomalies
        anomalies = self.performance_analyzer.detect_anomalies()
        if anomalies:
            self._handle_anomalies(anomalies)
            
        return metrics
        
    async def _collect_store_metrics(self, store: str) -> Dict:
        """Collect metrics for a specific store."""
        # Update resource metrics
        self.metrics_collector.update_resource_metrics(store)
        
        # Collect various metrics
        metrics = {
            "latency": {
                "avg": self.metrics_collector.search_latency.labels(
                    store=store,
                    query_type="search"
                )._sum.get() / max(1, self.metrics_collector.search_latency.labels(
                    store=store,
                    query_type="search"
                )._count.get()),
                "p95": self._calculate_percentile(store, 95),
                "p99": self._calculate_percentile(store, 99)
            },
            "throughput": {
                "current": self.metrics_collector.query_count.labels(
                    store=store,
                    query_type="search",
                    status="success"
                )._value.get(),
                "rate": self._calculate_query_rate(store)
            },
            "errors": {
                "count": self.metrics_collector.errors.labels(
                    store=store,
                    error_type="total"
                )._value.get(),
                "rate": self._calculate_error_rate(store)
            },
            "resources": {
                "memory_used": self.metrics_collector.memory_usage.labels(
                    store=store
                )._value.get(),
                "cpu_percent": self.metrics_collector.cpu_usage.labels(
                    store=store
                )._value.get(),
                "disk_used": self.metrics_collector.disk_usage.labels(
                    store=store,
                    type="used"
                )._value.get()
            },
            "cache": {
                "hit_rate": self._calculate_cache_hit_rate(store)
            }
        }
        
        return metrics
        
    def _calculate_percentile(self, store: str, percentile: float) -> float:
        """Calculate latency percentile."""
        # Implementation depends on histogram implementation
        pass
        
    def _calculate_query_rate(self, store: str) -> float:
        """Calculate current query rate."""
        # Implementation depends on counter implementation
        pass
        
    def _calculate_error_rate(self, store: str) -> float:
        """Calculate current error rate."""
        # Implementation depends on counter implementation
        pass
        
    def _calculate_cache_hit_rate(self, store: str) -> float:
        """Calculate cache hit rate."""
        hits = self.metrics_collector.cache_hits.labels(
            store=store,
            cache_type="total"
        )._value.get()
        
        misses = self.metrics_collector.cache_misses.labels(
            store=store,
            cache_type="total"
        )._value.get()
        
        total = hits + misses
        return hits / total if total > 0 else 0
        
    def _handle_anomalies(self, anomalies: Dict[str, List[Dict]]):
        """Handle detected anomalies."""
        for metric_type, metric_anomalies in anomalies.items():
            for anomaly in metric_anomalies:
                self.logger.warning(
                    f"Anomaly detected in {metric_type}: "
                    f"value={anomaly['value']:.2f}, "
                    f"mean={anomaly['mean']:.2f}, "
                    f"std={anomaly['std']:.2f}"
                )
