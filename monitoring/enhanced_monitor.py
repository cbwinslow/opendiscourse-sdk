import logging
import psutil
import time
import json
from dataclasses import dataclass, asdict
from typing import Dict, List, Optional
from datetime import datetime, timedelta
import requests
from collections import deque
import numpy as np

@dataclass
class PerformanceMetrics:
    """Detailed performance metrics for vector store operations."""
    query_latency_ms: float
    cpu_percent: float
    memory_percent: float
    disk_usage_percent: float
    network_bytes_sent: int
    network_bytes_recv: int
    timestamp: datetime

@dataclass
class StoreMetrics:
    """Metrics specific to individual vector stores."""
    store_name: str
    index_size: int
    vector_count: int
    operation_count: int
    error_count: int
    avg_latency_ms: float
    cache_hit_rate: float

class EnhancedMonitor:
    """Enhanced monitoring system with detailed metrics and alerting."""
    
    def __init__(self, config_path: str):
        """Initialize the enhanced monitoring system."""
        self.config = self._load_config(config_path)
        self.logger = self._setup_logger()
        
        # Initialize metrics storage
        self.performance_history = deque(maxlen=1000)  # Store last 1000 measurements
        self.store_metrics: Dict[str, StoreMetrics] = {}
        self.alert_history: List[Dict] = []
        
        # Initialize system monitoring
        self.cpu_tracker = psutil.cpu_percentages
        self.memory_tracker = psutil.virtual_memory
        self.disk_tracker = psutil.disk_usage('/')
        self.network_tracker = psutil.net_io_counters()
        
        # Initialize performance baselines
        self.latency_baseline = None
        self.error_rate_baseline = None
        
    def _load_config(self, config_path: str) -> Dict:
        """Load monitoring configuration."""
        with open(config_path, 'r') as f:
            return json.load(f)
            
    def _setup_logger(self) -> logging.Logger:
        """Set up enhanced logging system."""
        logger = logging.getLogger("vector_store_monitor")
        logger.setLevel(self.config["monitoring"]["log_level"])
        
        # Add file handler with rotation
        handler = logging.handlers.RotatingFileHandler(
            "logs/vector_store_monitor.log",
            maxBytes=10_000_000,  # 10MB
            backupCount=5
        )
        
        # Create formatter
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        
        return logger
        
    def record_operation_metrics(self, 
                               store_name: str,
                               operation_type: str,
                               latency_ms: float,
                               success: bool = True) -> None:
        """Record detailed metrics for a vector store operation."""
        # Get system metrics
        metrics = PerformanceMetrics(
            query_latency_ms=latency_ms,
            cpu_percent=psutil.cpu_percent(),
            memory_percent=psutil.virtual_memory().percent,
            disk_usage_percent=psutil.disk_usage('/').percent,
            network_bytes_sent=psutil.net_io_counters().bytes_sent,
            network_bytes_recv=psutil.net_io_counters().bytes_recv,
            timestamp=datetime.now()
        )
        
        # Update performance history
        self.performance_history.append(metrics)
        
        # Update store-specific metrics
        if store_name not in self.store_metrics:
            self.store_metrics[store_name] = StoreMetrics(
                store_name=store_name,
                index_size=0,
                vector_count=0,
                operation_count=0,
                error_count=0,
                avg_latency_ms=0,
                cache_hit_rate=0
            )
            
        store_metrics = self.store_metrics[store_name]
        store_metrics.operation_count += 1
        if not success:
            store_metrics.error_count += 1
            
        # Update average latency
        store_metrics.avg_latency_ms = (
            (store_metrics.avg_latency_ms * (store_metrics.operation_count - 1) +
             latency_ms) / store_metrics.operation_count
        )
        
        # Check thresholds and send alerts if needed
        self._check_thresholds(metrics, store_name)
        
    def _check_thresholds(self, 
                         metrics: PerformanceMetrics,
                         store_name: str) -> None:
        """Check if any metrics exceed configured thresholds."""
        thresholds = self.config["monitoring"]["thresholds"]
        
        alerts = []
        
        # Check CPU usage
        if metrics.cpu_percent > thresholds["cpu_usage_percent"]:
            alerts.append({
                "type": "cpu_usage",
                "value": metrics.cpu_percent,
                "threshold": thresholds["cpu_usage_percent"],
                "store": store_name
            })
            
        # Check memory usage
        if metrics.memory_percent > thresholds["memory_usage_percent"]:
            alerts.append({
                "type": "memory_usage",
                "value": metrics.memory_percent,
                "threshold": thresholds["memory_usage_percent"],
                "store": store_name
            })
            
        # Check disk usage
        if metrics.disk_usage_percent > thresholds["disk_usage_percent"]:
            alerts.append({
                "type": "disk_usage",
                "value": metrics.disk_usage_percent,
                "threshold": thresholds["disk_usage_percent"],
                "store": store_name
            })
            
        # Send alerts if needed
        for alert in alerts:
            self._send_alert(alert)
            
    def _send_alert(self, alert: Dict) -> None:
        """Send alert through configured channels."""
        alert["timestamp"] = datetime.now().isoformat()
        self.alert_history.append(alert)
        
        # Log alert
        self.logger.warning(f"Alert triggered: {alert}")
        
        # Send to configured channels
        alert_channels = self.config["monitoring"]["alert_channels"]
        
        # Email alerts
        if alert_channels["email"]["enabled"]:
            self._send_email_alert(alert)
            
        # Slack alerts
        if alert_channels["slack"]["enabled"]:
            self._send_slack_alert(alert)
            
    def _send_email_alert(self, alert: Dict) -> None:
        """Send alert via email."""
        # Implementation would depend on email service being used
        pass
        
    def _send_slack_alert(self, alert: Dict) -> None:
        """Send alert to Slack."""
        webhook_config = self.config["monitoring"]["alert_channels"]["slack"]
        
        with open(webhook_config["webhook_url"], 'r') as f:
            webhook_url = json.load(f)["url"]
            
        message = {
            "text": f"Vector Store Alert: {alert['type']}\n"
                   f"Store: {alert['store']}\n"
                   f"Value: {alert['value']}\n"
                   f"Threshold: {alert['threshold']}\n"
                   f"Time: {alert['timestamp']}"
        }
        
        try:
            requests.post(webhook_url, json=message)
        except Exception as e:
            self.logger.error(f"Failed to send Slack alert: {e}")
            
    def get_performance_summary(self) -> Dict:
        """Generate summary of recent performance metrics."""
        if not self.performance_history:
            return {}
            
        recent_metrics = list(self.performance_history)
        
        return {
            "latency": {
                "avg": np.mean([m.query_latency_ms for m in recent_metrics]),
                "p95": np.percentile([m.query_latency_ms for m in recent_metrics], 95),
                "p99": np.percentile([m.query_latency_ms for m in recent_metrics], 99)
            },
            "system": {
                "cpu_avg": np.mean([m.cpu_percent for m in recent_metrics]),
                "memory_avg": np.mean([m.memory_percent for m in recent_metrics]),
                "disk_avg": np.mean([m.disk_usage_percent for m in recent_metrics])
            },
            "network": {
                "bytes_sent_total": recent_metrics[-1].network_bytes_sent,
                "bytes_recv_total": recent_metrics[-1].network_bytes_recv
            },
            "time_range": {
                "start": recent_metrics[0].timestamp.isoformat(),
                "end": recent_metrics[-1].timestamp.isoformat()
            }
        }
        
    def detect_anomalies(self) -> List[Dict]:
        """Detect anomalies in performance metrics."""
        if len(self.performance_history) < 100:  # Need enough data
            return []
            
        anomalies = []
        recent_metrics = list(self.performance_history)
        
        # Calculate baselines if not set
        if self.latency_baseline is None:
            self.latency_baseline = np.mean([m.query_latency_ms for m in recent_metrics[:100]])
            
        # Check for latency anomalies (using 3-sigma rule)
        latencies = [m.query_latency_ms for m in recent_metrics]
        latency_std = np.std(latencies)
        recent_latency = latencies[-1]
        
        if abs(recent_latency - self.latency_baseline) > 3 * latency_std:
            anomalies.append({
                "type": "latency_anomaly",
                "value": recent_latency,
                "baseline": self.latency_baseline,
                "timestamp": recent_metrics[-1].timestamp.isoformat()
            })
            
        return anomalies
