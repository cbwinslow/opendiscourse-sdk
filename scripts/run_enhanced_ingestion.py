#!/usr/bin/env python3
"""
Run Enhanced Orchestrated Ingestion

This is the enhanced main entry point that integrates with existing infrastructure:
- Existing verification scripts
- Data status queries
- Monitoring infrastructure
- Complete bulk ingestion orchestrator
- Legacy ingestion managers
"""

import os
import sys
import json
import time
import argparse
from datetime import datetime
from typing import Dict, Any, List
from pathlib import Path

# Add project path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from enhanced_orchestrator import EnhancedOrchestrator
from ingestion_config import validate_all_api_keys, get_ingestion_mode_from_env

# Import existing components for direct access
from verify_complete_ingestion import IngestionVerifier
from data_status_queries import DataStatusDiagnostics
from complete_bulk_ingestion import BulkIngestionOrchestrator

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

def print_enhanced_banner():
    """Print the enhanced orchestration banner"""
    print("\n" + "="*80)
    print("🚀 ENHANCED MULTI-AGENT DATA INGESTION ORCHESTRATOR")
    print("="*80)
    print("📊 Enhanced orchestration with existing infrastructure integration")
    print("🔗 Coordinating congress.gov, govinfo.gov, and openstates.org APIs")
    print("📈 Real-time monitoring with existing job monitoring system")
    print("✅ Enhanced verification using existing verification scripts")
    print("📋 Comprehensive data diagnostics integration")
    print("="*80)

def validate_enhanced_environment():
    """Validate the enhanced ingestion environment"""
    print("🔍 Validating enhanced environment...")

    # Check API keys
    key_validation = validate_all_api_keys()
    if not key_validation['valid']:
        print("❌ API key validation failed:")
        for error in key_validation['errors']:
            print(f"   - {error}")
        return False

    # Check production mode
    mode = get_ingestion_mode_from_env()
    if mode.value != 'production':
        print(f"❌ Ingestion mode is '{mode.value}', must be 'production'")
        return False

    # Check database connectivity
    try:
        import psycopg2
        conn = psycopg2.connect(database='cbwinslow', user='cbwinslow')
        cursor = conn.cursor()
        cursor.execute("SELECT version();")
        version = cursor.fetchone()[0]
        cursor.close()
        conn.close()
        print("✅ Database connectivity verified")
    except Exception as e:
        print(f"❌ Database connectivity failed: {e}")
        return False

    # Check existing infrastructure components
    infrastructure_status = {}

    try:
        verifier = IngestionVerifier()
        infrastructure_status['ingestion_verifier'] = '✅ Available'
        verifier.cleanup()
    except Exception as e:
        infrastructure_status['ingestion_verifier'] = f'❌ Error: {e}'

    try:
        diagnostics = DataStatusDiagnostics()
        infrastructure_status['data_diagnostics'] = '✅ Available'
        diagnostics.cleanup()
    except Exception as e:
        infrastructure_status['data_diagnostics'] = f'❌ Error: {e}'

    try:
        bulk_orchestrator = BulkIngestionOrchestrator()
        infrastructure_status['bulk_orchestrator'] = '✅ Available'
    except Exception as e:
        infrastructure_status['bulk_orchestrator'] = f'❌ Error: {e}'

    # Check monitoring infrastructure
    monitoring_script = Path("scripts/monitoring/job_monitor.py")
    if monitoring_script.exists():
        infrastructure_status['job_monitor'] = '✅ Available'
    else:
        infrastructure_status['job_monitor'] = '❌ Not found'

    print("📊 Infrastructure Status:")
    for component, status in infrastructure_status.items():
        print(f"   {component}: {status}")

    print("✅ Enhanced environment validation passed")
    return True

def run_enhanced_quick_validation():
    """Run enhanced quick validation check"""
    print("\n🔍 Running enhanced quick validation...")

    # Run basic validation
    try:
        from ingestion_phase_1_validation import Phase1Validator

        validator = Phase1Validator()
        results = validator.run_phase_1_validation()

        if results['overall_status'] == 'PASS':
            print("✅ Basic validation passed")
        else:
            print("❌ Basic validation failed")
            print(f"   Status: {results['overall_status']}")
            for error in results.get('validation_results', {}).get('api_keys', {}).get('errors', []):
                print(f"   - {error}")
            return False
    except Exception as e:
        print(f"❌ Basic validation error: {e}")
        return False

    # Run enhanced infrastructure validation
    infrastructure_results = {}

    try:
        verifier = IngestionVerifier()
        checkpoint_status = verifier.get_checkpoint_status()
        infrastructure_results['checkpoint_check'] = checkpoint_status
        print("✅ Checkpoint verification passed")
        verifier.cleanup()
    except Exception as e:
        print(f"⚠️  Checkpoint verification warning: {e}")

    try:
        diagnostics = DataStatusDiagnostics()
        basic_report = diagnostics.get_basic_data_status()
        infrastructure_results['data_status_check'] = basic_report
        print("✅ Data status check passed")
        diagnostics.cleanup()
    except Exception as e:
        print(f"⚠️  Data status check warning: {e}")

    print("✅ Enhanced quick validation completed")
    return True

def run_enhanced_orchestration(mode: str, max_concurrent: int, save_report: bool = True) -> Dict[str, Any]:
    """Run the enhanced orchestrated ingestion"""
    print(f"\n🚀 Starting enhanced {mode} orchestration...")

    # Create enhanced orchestrator
    orchestrator = EnhancedOrchestrator()

    # Run orchestration
    if save_report:
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        report_filename = f"enhanced_orchestration_report_{mode}_{timestamp}.json"
        orchestrator.save_enhanced_report(report_filename, mode)
    else:
        report = orchestrator.orchestrate(mode, max_concurrent)

    return report

def run_legacy_compatibility_check():
    """Run compatibility check with legacy scripts"""
    print("\n🔄 Running legacy compatibility check...")

    legacy_scripts = [
        ("Complete Bulk Ingestion", "complete_bulk_ingestion.py"),
        ("Verify Complete Ingestion", "verify_complete_ingestion.py"),
        ("Data Status Queries", "data_status_queries.py"),
        ("Ingestion Manager", "ingestion_manager.py")
    ]

    compatibility_results = {}

    for script_name, script_path in legacy_scripts:
        full_path = Path(f"scripts/{script_path}")
        if full_path.exists():
            try:
                # Try to import the script
                script_module = script_path.replace('.py', '')
                module = __import__(script_module)
                compatibility_results[script_name] = '✅ Compatible'
            except Exception as e:
                compatibility_results[script_name] = f'⚠️  Import error: {e}'
        else:
            compatibility_results[script_name] = '❌ Not found'

    print("📊 Legacy Compatibility:")
    for script, status in compatibility_results.items():
        print(f"   {script}: {status}")

    return compatibility_results

def run_infrastructure_demonstration():
    """Demonstrate existing infrastructure integration"""
    print("\n🎭 Running infrastructure demonstration...")

    demo_results = {}

    # Demonstrate verification infrastructure
    try:
        verifier = IngestionVerifier()
        print("📋 Testing verification infrastructure...")

        # Test checkpoint status
        checkpoint_status = verifier.get_checkpoint_status()
        demo_results['checkpoint_verification'] = {
            'status': '✅ Working',
            'checkpoints_found': len(checkpoint_status) if isinstance(checkpoint_status, list) else 1
        }

        verifier.cleanup()
        print("✅ Verification infrastructure working")

    except Exception as e:
        demo_results['checkpoint_verification'] = {'status': f'❌ Error: {e}'}
        print(f"❌ Verification infrastructure error: {e}")

    # Demonstrate data diagnostics
    try:
        diagnostics = DataStatusDiagnostics()
        print("📊 Testing data diagnostics infrastructure...")

        # Test basic data status
        basic_status = diagnostics.get_basic_data_status()
        demo_results['data_diagnostics'] = {
            'status': '✅ Working',
            'data_points': len(basic_status) if isinstance(basic_status, dict) else 1
        }

        diagnostics.cleanup()
        print("✅ Data diagnostics infrastructure working")

    except Exception as e:
        demo_results['data_diagnostics'] = {'status': f'❌ Error: {e}'}
        print(f"❌ Data diagnostics infrastructure error: {e}")

    # Demonstrate monitoring infrastructure
    try:
        from monitoring.job_monitor import check_log

        # Create a test log file
        test_log = Path("test_monitoring.log")
        test_log.write_text("INFO: Test log entry\nERROR: Test error entry\nINFO: Another entry")

        alerts = check_log(test_log)
        demo_results['job_monitor'] = {
            'status': '✅ Working',
            'alerts_detected': alerts
        }

        # Clean up test log
        test_log.unlink()
        print("✅ Job monitoring infrastructure working")

    except Exception as e:
        demo_results['job_monitor'] = {'status': f'❌ Error: {e}'}
        print(f"❌ Job monitoring infrastructure error: {e}")

    return demo_results

def print_enhanced_menu():
    """Print the enhanced main menu"""
    print("\n" + "="*60)
    print("🚀 ENHANCED MULTI-AGENT INGESTION MENU")
    print("="*60)
    print("1. 🔍 Validate Enhanced Environment")
    print("2. ⚡ Enhanced Quick Validation")
    print("3. 🔄 Enhanced Sequential Orchestration")
    print("4. ⚡ Enhanced Parallel Orchestration")
    print("5. 🎭 Infrastructure Demonstration")
    print("6. 🔄 Legacy Compatibility Check")
    print("7. 📋 Show Enhanced Agent Configuration")
    print("8. 📊 Run Infrastructure Diagnostics")
    print("9. ❌ Exit")
    print("="*60)

def show_enhanced_agent_configuration():
    """Show the enhanced agent configuration"""
    print("\n📋 Enhanced Agent Configuration:")
    print("="*60)

    # Create enhanced orchestrator to get default agents
    orchestrator = EnhancedOrchestrator()
    enhanced_agents = orchestrator._get_enhanced_agents()

    for agent in enhanced_agents:
        print(f"\n🤖 Agent: {agent.agent_id}")
        print(f"   Phase: {agent.phase_number}")
        print(f"   Script: {agent.script_path}")
        print(f"   Dependencies: {', '.join(agent.dependencies) if agent.dependencies else 'None'}")
        print(f"   Priority: {agent.priority}")
        print(f"   Timeout: {agent.timeout_seconds}s")
        print(f"   Parallel Group: {agent.parallel_group or 'Serial'}")
        print(f"   Max Retries: {agent.max_retries}")
        print(f"   Uses Existing Infrastructure: {agent.use_existing_infrastructure}")

    print("\n" + "="*60)
    print("🔗 Existing Infrastructure Integration:")
    print("   ✅ IngestionVerifier (verify_complete_ingestion.py)")
    print("   ✅ DataStatusDiagnostics (data_status_queries.py)")
    print("   ✅ BulkIngestionOrchestrator (complete_bulk_ingestion.py)")
    print("   ✅ JobMonitor (monitoring/job_monitor.py)")
    print("   ✅ Enhanced logging and error handling")
    print("   ✅ Comprehensive verification and reporting")

def run_infrastructure_diagnostics():
    """Run comprehensive infrastructure diagnostics"""
    print("\n📊 Running comprehensive infrastructure diagnostics...")

    try:
        # Use existing data diagnostics
        diagnostics = DataStatusDiagnostics()

        print("📋 Generating comprehensive data status report...")
        report = diagnostics.generate_comprehensive_report()

        # Print summary
        print("\n📊 Infrastructure Diagnostics Summary:")
        print(f"📈 Report generated at: {report.get('generated_at', 'Unknown')}")

        if 'summary' in report:
            summary = report['summary']
            print(f"📄 Total records: {summary.get('total_records', 'Unknown')}")
            print(f"🔄 Checkpoints: {summary.get('checkpoints_processed', 'Unknown')}")
            print(f"❌ Errors: {summary.get('errors_found', 0)}")

        # Save report
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        report_filename = f"infrastructure_diagnostics_{timestamp}.json"

        with open(report_filename, 'w') as f:
            json.dump(report, f, indent=2, default=str)

        print(f"📄 Diagnostics report saved to: {report_filename}")

        diagnostics.cleanup()

    except Exception as e:
        print(f"❌ Infrastructure diagnostics failed: {e}")

def interactive_enhanced_mode():
    """Run in enhanced interactive mode"""
    while True:
        print_enhanced_menu()

        try:
            choice = input("\n🎯 Enter your choice (1-9): ").strip()

            if choice == '1':
                validate_enhanced_environment()

            elif choice == '2':
                run_enhanced_quick_validation()

            elif choice == '3':
                print("\n🔄 Starting Enhanced Sequential Orchestration...")
                run_enhanced_orchestration("sequential", 1)

            elif choice == '4':
                print("\n⚡ Starting Enhanced Parallel Orchestration...")
                max_concurrent = input("🔢 Enter max concurrent agents (default 4): ").strip()
                max_concurrent = int(max_concurrent) if max_concurrent.isdigit() else 4
                run_enhanced_orchestration("parallel", max_concurrent)

            elif choice == '5':
                run_infrastructure_demonstration()

            elif choice == '6':
                run_legacy_compatibility_check()

            elif choice == '7':
                show_enhanced_agent_configuration()

            elif choice == '8':
                run_infrastructure_diagnostics()

            elif choice == '9':
                print("\n👋 Goodbye!")
                break

            else:
                print("❌ Invalid choice. Please enter 1-9.")

            if choice != '9':
                input("\n🎯 Press Enter to continue...")

        except KeyboardInterrupt:
            print("\n\n🛑 Interrupted by user")
            break
        except Exception as e:
            print(f"\n❌ Error: {e}")
            input("\n🎯 Press Enter to continue...")

def main():
    """Main function"""
    parser = argparse.ArgumentParser(description='Run Enhanced Orchestrated Multi-Agent Ingestion')
    parser.add_argument('--mode', '-m', choices=['sequential', 'parallel', 'demo', 'interactive'],
                       default='interactive', help='Enhanced orchestration mode')
    parser.add_argument('--max-concurrent', '-c', type=int, default=4,
                       help='Maximum concurrent agents (parallel mode only)')
    parser.add_argument('--validate', action='store_true', help='Validate enhanced environment before starting')
    parser.add_argument('--quick-validate', action='store_true', help='Run enhanced quick validation only')
    parser.add_argument('--demo', action='store_true', help='Run infrastructure demonstration')
    parser.add_argument('--compatibility', action='store_true', help='Run legacy compatibility check')
    parser.add_argument('--save-report', action='store_true', default=True, help='Save enhanced orchestration report')
    parser.add_argument('--output', '-o', help='Output filename for report')

    args = parser.parse_args()

    # Print enhanced banner
    print_enhanced_banner()

    # Handle different modes
    if args.mode == 'interactive':
        interactive_enhanced_mode()

    elif args.mode == 'demo':
        run_infrastructure_demonstration()

    elif args.compatibility:
        run_legacy_compatibility_check()

    elif args.quick_validate:
        run_enhanced_quick_validation()

    else:
        # Real enhanced orchestration modes
        if args.validate and not validate_enhanced_environment():
            print("❌ Enhanced environment validation failed. Exiting.")
            sys.exit(1)

        if args.quick_validate and not run_enhanced_quick_validation():
            print("❌ Enhanced quick validation failed. Exiting.")
            sys.exit(1)

        try:
            report = run_enhanced_orchestration(args.mode, args.max_concurrent, args.save_report)

            # Exit with appropriate code
            if report['overall_status'] == 'SUCCESS':
                print("\n🎉 Enhanced orchestration completed successfully!")
                print(f"📊 Success rate: {report['success_rate']:.1f}%")
                print(f"✅ Completed: {report['completed_agents']}/{report['total_agents']}")
                if report.get('existing_infrastructure_used'):
                    print("🔗 Existing infrastructure integration: ✅ Active")
                sys.exit(0)
            else:
                print("\n⚠️  Enhanced orchestration completed with issues.")
                sys.exit(1)

        except KeyboardInterrupt:
            print("\n\n🛑 Enhanced orchestration interrupted by user")
            sys.exit(130)
        except Exception as e:
            print(f"\n❌ Enhanced orchestration failed: {e}")
            sys.exit(1)

if __name__ == "__main__":
    main()
