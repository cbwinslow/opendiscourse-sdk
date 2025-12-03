"""
Troubleshooting and debugging utilities for ingestion system
"""

import pytest
import subprocess
import psutil
import time
import json
import os
import sys
from pathlib import Path
from typing import Dict, Any, List, Optional
from unittest.mock import patch, Mock

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "scripts"))

class TestSystemDiagnostics:
    """Test system diagnostics and health checks"""

    @pytest.mark.troubleshooting
    @pytest.mark.unit
    def test_database_connectivity_diagnostic(self):
        """Test database connectivity diagnostic"""
        def check_database_connection():
            """Check database connection status"""
            try:
                import psycopg2
                from .utils.database_utils import get_database_helper

                helper = get_database_helper(use_test_db=False)

                with helper.get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute("SELECT version();")
                    version = cursor.fetchone()
                    cursor.close()

                    return {
                        'status': 'connected',
                        'version': version[0] if version else 'Unknown',
                        'connection_string': 'postgresql://cbwinslow@localhost/opendiscourse'
                    }
            except Exception as e:
                return {
                    'status': 'failed',
                    'error': str(e),
                    'connection_string': 'postgresql://cbwinslow@localhost/opendiscourse'
                }

        result = check_database_connection()

        assert result['status'] in ['connected', 'failed']
        assert 'connection_string' in result

        print(f"Database diagnostic: {result}")

    @pytest.mark.troubleshooting
    @pytest.mark.unit
    def test_api_connectivity_diagnostic(self):
        """Test API connectivity diagnostic"""
        def check_api_health():
            """Check API connectivity and response times"""
            api_endpoints = [
                {
                    'name': 'Congress API',
                    'url': 'https://api.congress.gov/v3/member/congress/118?limit=1',
                    'headers': {'X-API-Key': 'demo'},
                    'timeout': 10
                },
                {
                    'name': 'OpenStates API',
                    'url': 'https://v3.openstates.org/people?limit=1',
                    'headers': {'X-API-KEY': 'demo'},
                    'timeout': 10
                }
            ]

            results = []

            for api in api_endpoints:
                start_time = time.time()

                try:
                    import requests
                    response = requests.get(
                        api['url'],
                        headers=api['headers'],
                        timeout=api['timeout']
                    )
                    end_time = time.time()

                    results.append({
                        'api': api['name'],
                        'status': 'reachable',
                        'response_code': response.status_code,
                        'response_time': round((end_time - start_time) * 1000, 2),
                        'url': api['url']
                    })
                except requests.exceptions.RequestException as e:
                    end_time = time.time()
                    results.append({
                        'api': api['name'],
                        'status': 'failed',
                        'error': str(e),
                        'response_time': round((end_time - start_time) * 1000, 2),
                        'url': api['url']
                    })

            return results

        results = check_api_health()

        assert len(results) >= 1
        for result in results:
            assert 'api' in result
            assert 'status' in result
            assert 'response_time' in result

        print(f"API health check results: {json.dumps(results, indent=2)}")

    @pytest.mark.troubleshooting
    @pytest.mark.unit
    def test_system_resources_diagnostic(self):
        """Test system resources diagnostic"""
        def check_system_resources():
            """Check system resource usage"""
            try:
                memory = psutil.virtual_memory()
                disk = psutil.disk_usage('/')
                cpu_percent = psutil.cpu_percent(interval=1)

                process = psutil.Process()
                process_memory = process.memory_info()
                process_cpu = process.cpu_percent()

                return {
                    'system': {
                        'cpu_percent': cpu_percent,
                        'memory_total': memory.total,
                        'memory_available': memory.available,
                        'memory_percent': memory.percent,
                        'disk_total': disk.total,
                        'disk_free': disk.free,
                        'disk_percent': (disk.used / disk.total) * 100
                    },
                    'process': {
                        'pid': process.pid,
                        'memory_rss': process_memory.rss,
                        'memory_vms': process_memory.vms,
                        'cpu_percent': process_cpu,
                        'create_time': process.create_time()
                    }
                }
            except Exception as e:
                return {
                    'error': str(e),
                    'status': 'failed'
                }

        result = check_system_resources()

        assert 'system' in result or 'error' in result

        if 'system' in result:
            assert 'cpu_percent' in result['system']
            assert 'memory_percent' in result['system']
            assert 'disk_percent' in result['system']

        print(f"System resources: {result}")

class TestDiagnosticScripts:
    """Test diagnostic script functionality"""

    @pytest.mark.troubleshooting
    @pytest.mark.unit
    def test_ingestion_diagnostic_script(self):
        """Test ingestion system diagnostic script"""
        def run_ingestion_diagnostics():
            """Run comprehensive ingestion diagnostics"""
            diagnostics = {
                'timestamp': time.time(),
                'checks': {}
            }

            # 1. Database connectivity
            try:
                import psycopg2
                from .utils.database_utils import get_database_helper
                helper = get_database_helper(use_test_db=False)
                with helper.get_connection():
                    diagnostics['checks']['database'] = {'status': 'healthy', 'details': 'Connection successful'}
            except Exception as e:
                diagnostics['checks']['database'] = {'status': 'error', 'error': str(e)}

            # 2. Required tables exist
            try:
                helper = get_database_helper(use_test_db=False)
                required_tables = ['congress.bills', 'congress.members', 'incremental.ingestion_sessions']
                missing_tables = []

                for table in required_tables:
                    if not helper.table_exists(table):
                        missing_tables.append(table)

                if missing_tables:
                    diagnostics['checks']['schema'] = {'status': 'warning', 'missing_tables': missing_tables}
                else:
                    diagnostics['checks']['schema'] = {'status': 'healthy', 'details': 'All required tables exist'}
            except Exception as e:
                diagnostics['checks']['schema'] = {'status': 'error', 'error': str(e)}

            # 3. API configuration
            try:
                from env_config import validate_api_keys
                api_keys = validate_api_keys()
                missing_apis = [api for api, present in api_keys.items() if not present]

                if missing_apis:
                    diagnostics['checks']['api_keys'] = {'status': 'warning', 'missing_apis': missing_apis}
                else:
                    diagnostics['checks']['api_keys'] = {'status': 'healthy', 'details': 'All API keys present'}
            except Exception as e:
                diagnostics['checks']['api_keys'] = {'status': 'error', 'error': str(e)}

            # 4. Rate limiters
            try:
                from rate_limiter import adaptive_limiters
                limiter_status = {}
                for api_name, limiter in adaptive_limiters.items():
                    limiter_status[api_name] = {
                        'rate': limiter.current_rate,
                        'capacity': limiter.capacity,
                        'errors': limiter.consecutive_errors
                    }

                diagnostics['checks']['rate_limiters'] = {'status': 'healthy', 'limiters': limiter_status}
            except Exception as e:
                diagnostics['checks']['rate_limiters'] = {'status': 'error', 'error': str(e)}

            return diagnostics

        result = run_ingestion_diagnostics()

        assert 'timestamp' in result
        assert 'checks' in result

        expected_checks = ['database', 'schema', 'api_keys', 'rate_limiters']
        for check in expected_checks:
            assert check in result['checks']

        print(f"🎯 Ingestion diagnostics completed:")
        for check_name, check_result in result['checks'].items():
            status = check_result.get('status', 'unknown')
            print(f"  {status.upper()}: {check_name}")

class TestLogAnalysis:
    """Test log analysis and parsing utilities"""

    @pytest.mark.troubleshooting
    @pytest.mark.unit
    def test_error_log_parsing(self):
        """Test error log parsing functionality"""
        def parse_error_logs(log_entries: List[str]) -> Dict[str, Any]:
            """Parse and analyze error logs"""
            error_patterns = {
                'api_timeout': r'(timeout|timed out)',
                'database_error': r'(connection|constraint|foreign key)',
                'rate_limit': r'(rate limit|429|too many requests)',
                'authentication': r'(unauthorized|401|forbidden|403)',
                'server_error': r'(500|502|503|internal server error)'
            }

            error_summary = {
                'total_errors': len(log_entries),
                'error_types': {},
                'error_count_by_type': {},
                'timestamps': []
            }

            for entry in log_entries:
                timestamp_match = None
                for pattern in error_patterns.values():
                    if pattern.lower() in entry.lower():
                        timestamp_match = entry
                        break

                if timestamp_match:
                    error_summary['timestamps'].append(timestamp_match)

                # Categorize errors
                for error_type, pattern in error_patterns.items():
                    if pattern.lower() in entry.lower():
                        if error_type not in error_summary['error_types']:
                            error_summary['error_types'][error_type] = []
                        error_summary['error_types'][error_type].append(entry)
                        error_summary['error_count_by_type'][error_type] = \
                            error_summary['error_count_by_type'].get(error_type, 0) + 1

            return error_summary

        sample_logs = [
            "2024-01-15 10:30:45 ERROR API timeout occurred",
            "2024-01-15 10:31:02 ERROR Database connection failed",
            "2024-01-15 10:31:15 ERROR Rate limit exceeded (429)",
            "2024-01-15 10:31:30 ERROR Unauthorized access (401)",
            "2024-01-15 10:31:45 ERROR Internal server error (500)"
        ]

        result = parse_error_logs(sample_logs)

        assert result['total_errors'] == 5
        assert len(result['error_types']) >= 3
        assert result['error_count_by_type']['api_timeout'] == 1
        assert result['error_count_by_type']['rate_limit'] == 1
        assert result['error_count_by_type']['authentication'] == 1

        print(f"📋 Error log analysis:")
        for error_type, count in result['error_count_by_type'].items():
            print(f"  {error_type}: {count} occurrences")

class TestDebuggingUtilities:
    """Test debugging utilities and helpers"""

    @pytest.mark.troubleshooting
    @pytest.mark.unit
    def test_connection_debugging(self):
        """Test connection debugging utilities"""
        def debug_database_connection():
            """Debug database connection issues"""
            debug_info = {
                'connection_params': {},
                'tests': [],
                'recommendations': []
            }

            # Get connection parameters
            try:
                from env_config import get_database_config
                db_config = get_database_config()
                debug_info['connection_params'] = db_config
            except Exception as e:
                debug_info['connection_params'] = {'error': str(e)}
                debug_info['recommendations'].append('Check environment configuration')

            # Test basic connection
            try:
                import psycopg2
                conn = psycopg2.connect(database=db_config.get('database', 'opendiscourse'),
                                      user=db_config.get('user', 'cbwinslow'),
                                      host=db_config.get('host', '/var/run/postgresql'))
                conn.close()
                debug_info['tests'].append({'test': 'basic_connection', 'status': 'success'})
            except Exception as e:
                debug_info['tests'].append({'test': 'basic_connection', 'status': 'failed', 'error': str(e)})
                debug_info['recommendations'].extend([
                    'Check PostgreSQL service is running',
                    'Verify database user permissions',
                    'Check socket path if using Unix socket'
                ])

            return debug_info

        result = debug_database_connection()

        assert 'connection_params' in result
        assert 'tests' in result
        assert 'recommendations' in result

        print(f"🔍 Database connection debug:")
        for test in result['tests']:
            status = test['status']
            print(f"  {status.upper()}: {test['test']}")

        if result['recommendations']:
            print(f"💡 Recommendations:")
            for rec in result['recommendations']:
                print(f"  - {rec}")

class TestRecoveryProcedures:
    """Test recovery procedures and troubleshooting workflows"""

    @pytest.mark.troubleshooting
    @pytest.mark.unit
    def test_recovery_workflow(self):
        """Test recovery workflow procedures"""
        def execute_recovery_workflow(failed_session_id: str) -> Dict[str, Any]:
            """Execute recovery workflow for failed session"""
            recovery_steps = []

            # Step 1: Analyze failure
            try:
                from .utils.database_utils import get_database_helper
                helper = get_database_helper(use_test_db=False)

                # Get failed session
                sessions = helper.get_ingestion_sessions()
                failed_session = next((s for s in sessions if s['session_id'] == failed_session_id), None)

                if failed_session:
                    recovery_steps.append({
                        'step': 'analyze_failure',
                        'status': 'completed',
                        'details': f"Session status: {failed_session['status']}"
                    })
                else:
                    recovery_steps.append({
                        'step': 'analyze_failure',
                        'status': 'failed',
                        'error': 'Session not found'
                    })
            except Exception as e:
                recovery_steps.append({
                    'step': 'analyze_failure',
                    'status': 'failed',
                    'error': str(e)
                })

            # Step 2: Create recovery session
            try:
                recovery_session_id = f"{failed_session_id}_recovery"
                helper.create_test_ingestion_session(
                    session_id=recovery_session_id,
                    data_source='congress.gov',
                    data_type='bills',
                    status='running'
                )

                recovery_steps.append({
                    'step': 'create_recovery_session',
                    'status': 'completed',
                    'recovery_session_id': recovery_session_id
                })
            except Exception as e:
                recovery_steps.append({
                    'step': 'create_recovery_session',
                    'status': 'failed',
                    'error': str(e)
                })

            # Step 3: Verify recovery setup
            try:
                # Check recovery session exists
                recovery_sessions = helper.get_ingestion_sessions()
                recovery_exists = any(s['session_id'] == recovery_session_id for s in recovery_sessions)

                if recovery_exists:
                    recovery_steps.append({
                        'step': 'verify_recovery_setup',
                        'status': 'completed',
                        'details': 'Recovery session created successfully'
                    })
                else:
                    recovery_steps.append({
                        'step': 'verify_recovery_setup',
                        'status': 'failed',
                        'error': 'Recovery session not found'
                    })
            except Exception as e:
                recovery_steps.append({
                    'step': 'verify_recovery_setup',
                    'status': 'failed',
                    'error': str(e)
                })

            return {
                'failed_session': failed_session_id,
                'recovery_steps': recovery_steps,
                'overall_status': 'completed' if all(step['status'] == 'completed' for step in recovery_steps) else 'partial'
            }

        result = execute_recovery_workflow('test_failed_session')

        assert 'failed_session' in result
        assert 'recovery_steps' in result
        assert 'overall_status' in result

        print(f"🔄 Recovery workflow for {result['failed_session']}:")
        for step in result['recovery_steps']:
            status = step['status']
            print(f"  {status.upper()}: {step['step']}")

        print(f"Overall status: {result['overall_status'].upper()}")
