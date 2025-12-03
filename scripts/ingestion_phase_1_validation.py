#!/usr/bin/env python3
"""
Phase 1: API Key Validation and Environment Setup

This script handles the critical first phase of any data ingestion process:
- Validates all API keys are present and working
- Ensures production mode is active
- Verifies database connectivity
- Sets up monitoring infrastructure

ASSIGNED TO: AI Agent responsible for validation and setup
DEPENDENCIES: None (this must run first)
"""

import os
import sys
import json
import psycopg2
from datetime import datetime
from typing import Dict, Any, List

# Add project path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from ingestion_config import validate_all_api_keys, get_ingestion_mode_from_env

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

class Phase1Validator:
    """Phase 1: API Key Validation and Environment Setup"""

    def __init__(self):
        self.phase_start = datetime.now()
        self.validation_results = {}
        self.setup_complete = False

    def validate_api_keys(self) -> Dict[str, Any]:
        """Validate all required API keys"""
        print("🔑 Phase 1.1: Validating API Keys...")

        try:
            validation = validate_all_api_keys()

            self.validation_results['api_keys'] = {
                'status': 'PASS' if validation['valid'] else 'FAIL',
                'errors': validation.get('errors', []),
                'timestamp': datetime.now().isoformat()
            }

            if validation['valid']:
                print("✅ All API keys are valid")
                return True
            else:
                print("❌ API key validation failed:")
                for error in validation['errors']:
                    print(f"   - {error}")
                return False

        except Exception as e:
            print(f"❌ Error validating API keys: {e}")
            self.validation_results['api_keys'] = {
                'status': 'ERROR',
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }
            return False

    def validate_ingestion_mode(self) -> Dict[str, Any]:
        """Validate ingestion mode is production"""
        print("🚀 Phase 1.2: Validating Ingestion Mode...")

        try:
            mode = get_ingestion_mode_from_env()

            mode_valid = mode.value == 'production'
            self.validation_results['ingestion_mode'] = {
                'status': 'PASS' if mode_valid else 'FAIL',
                'current_mode': mode.value,
                'required_mode': 'production',
                'timestamp': datetime.now().isoformat()
            }

            if mode_valid:
                print(f"✅ Ingestion mode: {mode.value}")
                return True
            else:
                print(f"❌ Invalid ingestion mode: {mode.value} (required: production)")
                return False

        except Exception as e:
            print(f"❌ Error validating ingestion mode: {e}")
            self.validation_results['ingestion_mode'] = {
                'status': 'ERROR',
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }
            return False

    def validate_database_connectivity(self) -> Dict[str, Any]:
        """Validate database connectivity"""
        print("🗄️  Phase 1.3: Validating Database Connectivity...")

        try:
            conn = psycopg2.connect(database='cbwinslow', user='cbwinslow')
            cursor = conn.cursor()

            # Test basic query
            cursor.execute("SELECT version();")
            version = cursor.fetchone()[0]

            cursor.close()
            conn.close()

            self.validation_results['database'] = {
                'status': 'PASS',
                'version': version,
                'timestamp': datetime.now().isoformat()
            }

            print("✅ Database connectivity verified")
            return True

        except Exception as e:
            print(f"❌ Database connectivity failed: {e}")
            self.validation_results['database'] = {
                'status': 'FAIL',
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }
            return False

    def validate_monitoring_setup(self) -> Dict[str, Any]:
        """Validate monitoring infrastructure"""
        print("📊 Phase 1.4: Validating Monitoring Setup...")

        try:
            # Check if monitoring modules can be imported
            from monitoring.job_monitor import JobMonitor

            # Test basic monitoring initialization
            monitor = JobMonitor("validation_test")

            self.validation_results['monitoring'] = {
                'status': 'PASS',
                'monitor_type': type(monitor).__name__,
                'timestamp': datetime.now().isoformat()
            }

            print("✅ Monitoring infrastructure ready")
            return True

        except Exception as e:
            print(f"❌ Monitoring setup failed: {e}")
            self.validation_results['monitoring'] = {
                'status': 'FAIL',
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }
            return False

    def validate_disk_space(self) -> Dict[str, Any]:
        """Validate sufficient disk space for ingestion"""
        print("💾 Phase 1.5: Validating Disk Space...")

        try:
            import shutil

            # Check available disk space
            total, used, free = shutil.disk_usage("/")
            free_gb = free // (1024**3)

            # Require at least 10GB free space
            space_sufficient = free_gb >= 10

            self.validation_results['disk_space'] = {
                'status': 'PASS' if space_sufficient else 'FAIL',
                'free_gb': free_gb,
                'required_gb': 10,
                'timestamp': datetime.now().isoformat()
            }

            if space_sufficient:
                print(f"✅ Disk space: {free_gb}GB available")
                return True
            else:
                print(f"❌ Insufficient disk space: {free_gb}GB available (10GB required)")
                return False

        except Exception as e:
            print(f"❌ Error checking disk space: {e}")
            self.validation_results['disk_space'] = {
                'status': 'ERROR',
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }
            return False

    def run_phase_1_validation(self) -> Dict[str, Any]:
        """Run complete Phase 1 validation"""
        print("\n" + "="*60)
        print("🚀 PHASE 1: VALIDATION AND SETUP")
        print("="*60)

        validation_steps = [
            self.validate_api_keys,
            self.validate_ingestion_mode,
            self.validate_database_connectivity,
            self.validate_monitoring_setup,
            self.validate_disk_space
        ]

        all_passed = True
        for step in validation_steps:
            if not step():
                all_passed = False

        self.setup_complete = all_passed

        # Generate summary
        summary = {
            'phase': 1,
            'phase_name': 'Validation and Setup',
            'start_time': self.phase_start.isoformat(),
            'end_time': datetime.now().isoformat(),
            'duration_seconds': (datetime.now() - self.phase_start).total_seconds(),
            'overall_status': 'PASS' if all_passed else 'FAIL',
            'validation_results': self.validation_results,
            'setup_complete': self.setup_complete
        }

        print("\n" + "="*60)
        print(f"📊 PHASE 1 SUMMARY: {summary['overall_status']}")
        print(f"⏱️  Duration: {summary['duration_seconds']:.2f} seconds")
        print(f"🎯 Setup Complete: {'✅' if self.setup_complete else '❌'}")
        print("="*60)

        return summary

    def save_validation_results(self, filename: str = None) -> str:
        """Save validation results to file"""
        if not filename:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"phase_1_validation_{timestamp}.json"

        summary = self.run_phase_1_validation()

        try:
            with open(filename, 'w') as f:
                json.dump(summary, f, indent=2, default=str)

            print(f"📄 Validation results saved to: {filename}")
            return filename

        except Exception as e:
            print(f"❌ Error saving validation results: {e}")
            return ""

def main():
    """Main function"""
    import argparse

    parser = argparse.ArgumentParser(description='Phase 1: API Key Validation and Setup')
    parser.add_argument('--output', '-o', help='Output filename (default: auto-generated)')
    parser.add_argument('--save', action='store_true', help='Save results to file')

    args = parser.parse_args()

    try:
        validator = Phase1Validator()

        if args.save:
            validator.save_validation_results(args.output)
        else:
            validator.run_phase_1_validation()

        # Exit with appropriate code
        sys.exit(0 if validator.setup_complete else 1)

    except Exception as e:
        print(f"❌ Phase 1 validation failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
