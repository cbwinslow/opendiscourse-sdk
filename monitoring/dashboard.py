import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import asyncio
from typing import Dict, List
import json

from monitoring.enhanced_monitor import EnhancedMonitor
from monitoring.health_checks import EnhancedHealthChecker

class MonitoringDashboard:
    def __init__(self, config_path: str):
        """Initialize the monitoring dashboard."""
        self.config_path = config_path
        self.monitor = EnhancedMonitor(config_path)
        with open(config_path, 'r') as f:
            self.config = json.load(f)
        self.health_checker = EnhancedHealthChecker(self.config)
        
    def render_dashboard(self):
        """Render the main dashboard."""
        st.set_page_config(page_title="Vector Store Monitor", layout="wide")
        st.title("Vector Store Monitoring Dashboard")
        
        # Sidebar for filters and settings
        self._render_sidebar()
        
        # Main dashboard layout
        col1, col2 = st.columns(2)
        
        with col1:
            self._render_health_status()
            self._render_performance_metrics()
            
        with col2:
            self._render_store_metrics()
            self._render_anomaly_detection()
            
        # Bottom section for detailed logs and alerts
        st.markdown("---")
        self._render_logs_and_alerts()
        
    def _render_sidebar(self):
        """Render sidebar with filters and settings."""
        st.sidebar.title("Dashboard Controls")
        
        # Time range selector
        st.sidebar.subheader("Time Range")
        time_range = st.sidebar.selectbox(
            "Select time range",
            ["Last Hour", "Last 24 Hours", "Last 7 Days", "Custom"]
        )
        
        if time_range == "Custom":
            start_date = st.sidebar.date_input("Start date")
            end_date = st.sidebar.date_input("End date")
            
        # Store selector
        st.sidebar.subheader("Vector Stores")
        stores = list(self.config["stores"].keys())
        selected_stores = st.sidebar.multiselect(
            "Select stores to display",
            stores,
            default=stores
        )
        
        # Metric thresholds
        st.sidebar.subheader("Alert Thresholds")
        error_rate = st.sidebar.slider(
            "Error Rate Threshold (%)",
            0.0, 100.0,
            value=float(self.config["monitoring"]["thresholds"]["error_rate"] * 100)
        )
        latency_ms = st.sidebar.slider(
            "Latency Threshold (ms)",
            0, 5000,
            value=int(self.config["monitoring"]["thresholds"]["latency_ms"])
        )
        
        # Auto-refresh toggle
        st.sidebar.subheader("Settings")
        auto_refresh = st.sidebar.checkbox("Auto-refresh", value=True)
        if auto_refresh:
            refresh_interval = st.sidebar.number_input(
                "Refresh interval (seconds)",
                min_value=5,
                value=30
            )
            
    def _render_health_status(self):
        """Render health status cards for all stores."""
        st.subheader("Health Status")
        
        # Get current health status
        health_status = asyncio.run(self.health_checker.run_diagnostics())
        
        # Create status cards
        cols = st.columns(len(self.config["stores"]))
        for i, (store_name, status) in enumerate(health_status["stores"].items()):
            with cols[i]:
                color = "green" if status["status"] == "healthy" else "red"
                st.markdown(
                    f"""
                    <div style="padding: 20px; border-radius: 10px; background-color: {color}25;">
                        <h3 style="color: {color};">{store_name}</h3>
                        <p>Status: {status["status"].upper()}</p>
                        <p>Latency: {status["latency_ms"]:.2f}ms</p>
                    </div>
                    """,
                    unsafe_allow_html=True
                )
                
    def _render_performance_metrics(self):
        """Render performance metrics charts."""
        st.subheader("Performance Metrics")
        
        # Get performance data
        metrics = self.monitor.get_performance_summary()
        
        # Create latency chart
        fig_latency = go.Figure()
        fig_latency.add_trace(go.Scatter(
            y=[m["latency"]["avg"] for m in metrics],
            name="Average Latency"
        ))
        fig_latency.add_trace(go.Scatter(
            y=[m["latency"]["p95"] for m in metrics],
            name="95th Percentile"
        ))
        fig_latency.update_layout(title="Latency Over Time")
        st.plotly_chart(fig_latency)
        
        # Create system metrics chart
        fig_system = go.Figure()
        fig_system.add_trace(go.Scatter(
            y=[m["system"]["cpu_avg"] for m in metrics],
            name="CPU Usage"
        ))
        fig_system.add_trace(go.Scatter(
            y=[m["system"]["memory_avg"] for m in metrics],
            name="Memory Usage"
        ))
        fig_system.update_layout(title="System Resource Usage")
        st.plotly_chart(fig_system)
        
    def _render_store_metrics(self):
        """Render store-specific metrics."""
        st.subheader("Store Metrics")
        
        # Get store metrics
        store_metrics = self.monitor.store_metrics
        
        for store_name, metrics in store_metrics.items():
            with st.expander(f"{store_name} Metrics"):
                cols = st.columns(4)
                cols[0].metric("Total Operations", metrics.operation_count)
                cols[1].metric("Error Count", metrics.error_count)
                cols[2].metric("Avg Latency", f"{metrics.avg_latency_ms:.2f}ms")
                cols[3].metric("Cache Hit Rate", f"{metrics.cache_hit_rate:.1%}")
                
                # Show trend chart
                df = pd.DataFrame({
                    "timestamp": self.monitor.performance_history.timestamp,
                    "latency": self.monitor.performance_history.query_latency_ms
                })
                fig = px.line(df, x="timestamp", y="latency", title="Operation Latency Trend")
                st.plotly_chart(fig)
                
    def _render_anomaly_detection(self):
        """Render anomaly detection results."""
        st.subheader("Anomaly Detection")
        
        # Get anomalies
        anomalies = self.monitor.detect_anomalies()
        
        if anomalies:
            for anomaly in anomalies:
                st.error(
                    f"""
                    Anomaly detected: {anomaly['type']}
                    - Value: {anomaly['value']:.2f}
                    - Baseline: {anomaly['baseline']:.2f}
                    - Time: {anomaly['timestamp']}
                    """
                )
        else:
            st.success("No anomalies detected")
            
    def _render_logs_and_alerts(self):
        """Render logs and alerts section."""
        tab1, tab2 = st.tabs(["Logs", "Alerts"])
        
        with tab1:
            st.subheader("System Logs")
            logs = self._get_recent_logs()
            for log in logs:
                severity_color = {
                    "INFO": "blue",
                    "WARNING": "orange",
                    "ERROR": "red"
                }.get(log["level"], "gray")
                
                st.markdown(
                    f"""
                    <div style="color: {severity_color};">
                        [{log['timestamp']}] {log['level']}: {log['message']}
                    </div>
                    """,
                    unsafe_allow_html=True
                )
                
        with tab2:
            st.subheader("Recent Alerts")
            alerts = self.monitor.alert_history
            for alert in alerts:
                st.warning(
                    f"""
                    Alert: {alert['type']}
                    Store: {alert['store']}
                    Value: {alert['value']}
                    Threshold: {alert['threshold']}
                    Time: {alert['timestamp']}
                    """
                )
                
    def _get_recent_logs(self) -> List[Dict]:
        """Get recent logs from the log file."""
        logs = []
        try:
            with open("logs/vector_store_monitor.log", "r") as f:
                for line in f.readlines()[-100:]:  # Last 100 lines
                    parts = line.split(" - ")
                    if len(parts) >= 3:
                        logs.append({
                            "timestamp": parts[0],
                            "level": parts[1],
                            "message": " - ".join(parts[2:]).strip()
                        })
        except Exception as e:
            st.error(f"Error reading logs: {e}")
        return logs

def main():
    """Main function to run the dashboard."""
    dashboard = MonitoringDashboard("config/vector_store/config.json")
    dashboard.render_dashboard()

if __name__ == "__main__":
    main()
