import json
import logging
import os
from dataclasses import dataclass
from enum import Enum
from typing import Dict, List, Optional
from datetime import datetime

# Health Status Enum
class HealthStatus(Enum):
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"

@dataclass
class StoreConnection:
    host: str
    port: int
    database: str
    credentials_path: Optional[str] = None

@dataclass
class VectorStoreSettings:
    dimension: int
    metric: str
    index_type: str
    stores: Dict[str, StoreConnection]

class VectorStoreConfig:
    def __init__(self, config_path: str):
        """Initialize vector store configuration from a JSON config file.
        
        Args:
            config_path: Path to the JSON configuration file
        """
        self.config_path = config_path
        self.settings: Optional[VectorStoreSettings] = None
        self.connections: Dict[str, object] = {}
        
        # Load and validate configuration
        self._load_configuration()
        self._validate_settings()
        self._initialize_connections()
    
    def _load_configuration(self) -> None:
        """Load configuration from JSON file."""
        if not os.path.exists(self.config_path):
            raise FileNotFoundError(f"Config file not found: {self.config_path}")
            
        try:
            with open(self.config_path, 'r') as f:
                config_data = json.load(f)
                
            # Parse store connections
            stores = {}
            for store_name, store_config in config_data.get("stores", {}).items():
                stores[store_name] = StoreConnection(**store_config)
            
            # Create settings object
            self.settings = VectorStoreSettings(
                dimension=config_data["dimension"],
                metric=config_data["metric"],
                index_type=config_data["index_type"],
                stores=stores
            )
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON in config file: {e}")
        except KeyError as e:
            raise ValueError(f"Missing required configuration key: {e}")
    
    def _validate_settings(self) -> None:
        """Validate the loaded configuration settings."""
        if not self.settings:
            raise ValueError("Configuration not loaded")
            
        # Validate dimension
        if self.settings.dimension <= 0:
            raise ValueError("Vector dimension must be positive")
            
        # Validate metric type
        valid_metrics = ["euclidean", "cosine", "dot_product"]
        if self.settings.metric not in valid_metrics:
            raise ValueError(f"Invalid metric type. Must be one of: {valid_metrics}")
            
        # Validate store configurations
        for store_name, store_conn in self.settings.stores.items():
            if not store_conn.host:
                raise ValueError(f"Missing host for store: {store_name}")
            if store_conn.port <= 0 or store_conn.port > 65535:
                raise ValueError(f"Invalid port for store: {store_name}")
    
    def _initialize_connections(self) -> None:
        """Initialize connections to all configured vector stores."""
        # This would be implemented based on specific vector store client libraries
        # For example, using Milvus, FAISS, or other vector store clients
        pass

class SystemMonitor:
    def __init__(self):
        """Initialize system monitoring and logging."""
        # Set up logging
        self.logger = logging.getLogger("vector_store_monitor")
        self.logger.setLevel(logging.INFO)
        
        # Create handlers
        console_handler = logging.StreamHandler()
        file_handler = logging.FileHandler("vector_store.log")
        
        # Create formatters and add to handlers
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        console_handler.setFormatter(formatter)
        file_handler.setFormatter(formatter)
        
        # Add handlers to logger
        self.logger.addHandler(console_handler)
        self.logger.addHandler(file_handler)
        
        # Initialize metrics storage
        self.metrics = {
            "queries_total": 0,
            "inserts_total": 0,
            "query_latency": [],
            "insert_latency": [],
            "errors_total": 0,
            "last_error_time": None
        }
        
        # Configure alerts
        self.alert_thresholds = {
            "error_rate": 0.05,  # 5% error rate threshold
            "latency_ms": 1000,  # 1 second latency threshold
            "memory_usage_percent": 90  # 90% memory usage threshold
        }
    
    def record_query(self, latency_ms: float) -> None:
        """Record a query operation and its latency."""
        self.metrics["queries_total"] += 1
        self.metrics["query_latency"].append(latency_ms)
        
        # Check for latency alerts
        if latency_ms > self.alert_thresholds["latency_ms"]:
            self.logger.warning(f"High query latency detected: {latency_ms}ms")
    
    def record_insert(self, latency_ms: float) -> None:
        """Record an insert operation and its latency."""
        self.metrics["inserts_total"] += 1
        self.metrics["insert_latency"].append(latency_ms)
        
        # Check for latency alerts
        if latency_ms > self.alert_thresholds["latency_ms"]:
            self.logger.warning(f"High insert latency detected: {latency_ms}ms")
    
    def record_error(self, error: Exception) -> None:
        """Record an error event."""
        self.metrics["errors_total"] += 1
        self.metrics["last_error_time"] = datetime.now()
        
        # Log the error
        self.logger.error(f"Vector store error: {str(error)}")
        
        # Check error rate
        total_ops = self.metrics["queries_total"] + self.metrics["inserts_total"]
        if total_ops > 0:
            error_rate = self.metrics["errors_total"] / total_ops
            if error_rate > self.alert_thresholds["error_rate"]:
                self.logger.critical(f"High error rate detected: {error_rate:.2%}")

class HealthChecker:
    def __init__(self, config: VectorStoreConfig, monitor: SystemMonitor):
        """Initialize health checker with config and monitor references."""
        self.config = config
        self.monitor = monitor
        self.logger = monitor.logger
    
    def check_health(self) -> HealthStatus:
        """Check the health of all vector store components.
        
        Returns:
            HealthStatus: Current health status of the system
        """
        try:
            # Check all vector stores
            store_statuses = self._check_stores()
            
            # Check monitoring system
            monitoring_status = self._check_monitoring()
            
            # Check basic operations
            operations_status = self._check_operations()
            
            # Aggregate health status
            if not all(status == HealthStatus.HEALTHY for status in [
                *store_statuses.values(),
                monitoring_status,
                operations_status
            ]):
                return HealthStatus.UNHEALTHY
            
            # Check for degraded performance
            if self._is_performance_degraded():
                return HealthStatus.DEGRADED
            
            return HealthStatus.HEALTHY
            
        except Exception as e:
            self.logger.error(f"Health check failed: {str(e)}")
            return HealthStatus.UNHEALTHY
    
    def _check_stores(self) -> Dict[str, HealthStatus]:
        """Check health of all configured vector stores."""
        store_statuses = {}
        for store_name, store_conn in self.config.settings.stores.items():
            try:
                # This would implement specific health checks for each store type
                # For example: ping, connection test, basic query
                store_statuses[store_name] = HealthStatus.HEALTHY
            except Exception as e:
                self.logger.error(f"Store {store_name} health check failed: {str(e)}")
                store_statuses[store_name] = HealthStatus.UNHEALTHY
        
        return store_statuses
    
    def _check_monitoring(self) -> HealthStatus:
        """Check health of monitoring system."""
        try:
            # Verify logger is working
            self.logger.debug("Monitoring system health check")
            
            # Verify metrics are being collected
            if not all(key in self.monitor.metrics for key in [
                "queries_total",
                "inserts_total",
                "errors_total"
            ]):
                return HealthStatus.UNHEALTHY
            
            return HealthStatus.HEALTHY
        except Exception:
            return HealthStatus.UNHEALTHY
    
    def _check_operations(self) -> HealthStatus:
        """Check basic operations are working."""
        try:
            # This would implement basic CRUD operation tests
            # For example: insert test vector, query test vector, delete test vector
            return HealthStatus.HEALTHY
        except Exception:
            return HealthStatus.UNHEALTHY
    
    def _is_performance_degraded(self) -> bool:
        """Check if system performance is degraded."""
        if not self.monitor.metrics["query_latency"]:
            return False
            
        # Calculate average latency
        avg_latency = sum(self.monitor.metrics["query_latency"]) / len(
            self.monitor.metrics["query_latency"]
        )
        
        # Check if average latency exceeds threshold
        return avg_latency > self.monitor.alert_thresholds["latency_ms"]
