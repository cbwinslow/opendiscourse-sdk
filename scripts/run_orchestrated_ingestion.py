#!/usr/bin/env python3
"""
Run Orchestrated Ingestion

This is the main entry point for running orchestrated multi-agent data ingestion.
It provides a simple interface to start, monitor, and manage the complete ingestion process.
"""

import argparse
import os
import sys
import time
from datetime import datetime
from typing import Any, Dict

# Add project path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
# Load environment variables
from dotenv import load_dotenv
from ingestion_config import get_ingestion_mode_from_env, validate_all_api_keys
from orchestrator_framework import Orchestrator

load_dotenv()

def print_banner():
    """Print the orchestration banner"""
    print("\n" + "="*80)
    print("🚀 MULTI-AGENT DATA INGESTION ORCHESTRATOR")
    print("="*80)
    print("📊 Orchestrating parallel data ingestion across multiple AI agents")
    print("🔗 Coordinating congress.gov, govinfo.gov, and openstates.org APIs")
    print("📈 Real-time progress monitoring and error handling")
    print("="*80)

def validate_environment():
    """Validate the ingestion environment"""
    print("🔍 Validating environment...")

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

    print("✅ Environment validation passed")
    return True

def run_quick_validation():
    """Run a quick validation check"""
    print("\n🔍 Running quick validation...")

    # Import and run phase 1 validation
    try:
        from ingestion_phase_1_validation import Phase1Validator

        validator = Phase1Validator()
        results = validator.run_phase_1_validation()

        if results['overall_status'] == 'PASS':
            print("✅ Quick validation passed")
            return True
        else:
            print("❌ Quick validation failed")
            print(f"   Status: {results['overall_status']}")
            for error in results.get('validation_results', {}).get('api_keys', {}).get('errors', []):
                print(f"   - {error}")
            return False

    except Exception as e:
        print(f"❌ Quick validation error: {e}")
        return False

def run_orchestration(mode: str, max_concurrent: int, save_report: bool = True) -> Dict[str, Any]:
    """Run the orchestrated ingestion"""
    print(f"\n🚀 Starting {mode} orchestration...")

    # Create orchestrator
    orchestrator = Orchestrator()

    # Run orchestration
    if save_report:
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        report_filename = f"orchestration_report_{mode}_{timestamp}.json"
        orchestrator.save_orchestration_report(report_filename, mode)
    else:
        report = orchestrator.orchestrate(mode, max_concurrent)

    return report

def run_sequential_demo():
    """Run a sequential demonstration"""
    print("\n🔄 Running sequential demonstration...")

    # Import individual phase scripts
    phases = [
        ("Phase 1: Validation", "ingestion_phase_1_validation.py"),
        ("Phase 2: Congress Members", "ingestion_phase_2_congress_members.py"),
        ("Phase 3: Congress Bills", "ingestion_phase_3_congress_bills.py"),
        ("Phase 4: GovInfo Bills", "ingestion_phase_4_govinfo_bills.py"),
        ("Phase 5: OpenStates", "ingestion_phase_5_openstates.py"),
        ("Phase 6: Verification", "ingestion_phase_6_verification.py")
    ]

    start_time = datetime.now()
    completed_phases = []
    failed_phases = []

    for phase_name, script_name in phases:
        print(f"\n📋 {phase_name}")
        print(f"📜 Script: {script_name}")

        phase_start = datetime.now()

        try:
            # Import and run the phase
            script_module = script_name.replace('.py', '')
            phase_module = __import__(script_module)

            # Run the phase (this would need to be implemented in each script)
            print(f"🚀 Starting {phase_name}...")

            # Simulate execution for demo
            time.sleep(2)

            phase_end = datetime.now()
            duration = (phase_end - phase_start).total_seconds()

            completed_phases.append({
                'phase': phase_name,
                'script': script_name,
                'duration_seconds': duration,
                'status': 'COMPLETED'
            })

            print(f"✅ {phase_name} completed in {duration:.1f}s")

        except Exception as e:
            print(f"❌ {phase_name} failed: {e}")
            failed_phases.append({
                'phase': phase_name,
                'script': script_name,
                'error': str(e),
                'status': 'FAILED'
            })

    total_duration = (datetime.now() - start_time).total_seconds()

    # Generate demo report
    demo_report = {
        'mode': 'sequential_demo',
        'start_time': start_time.isoformat(),
        'end_time': datetime.now().isoformat(),
        'duration_seconds': total_duration,
        'total_phases': len(phases),
        'completed_phases': len(completed_phases),
        'failed_phases': len(failed_phases),
        'success_rate': (len(completed_phases) / len(phases) * 100),
        'completed_phases_details': completed_phases,
        'failed_phases_details': failed_phases,
        'overall_status': 'SUCCESS' if len(failed_phases) == 0 else 'PARTIAL_SUCCESS'
    }

    print("\n📊 Sequential Demo Results:")
    print(f"✅ Completed: {len(completed_phases)}/{len(phases)} phases")
    print(f"❌ Failed: {len(failed_phases)}/{len(phases)} phases")
    print(f"⏱️  Total Duration: {total_duration:.1f}s")
    print(f"📈 Success Rate: {demo_report['success_rate']:.1f}%")

    return demo_report

def run_parallel_demo():
    """Run a parallel demonstration"""
    print("\n⚡ Running parallel demonstration...")

    # Define parallel groups
    parallel_groups = {
        'validation': ['Phase 1: Validation'],
        'data_ingestion': [
            'Phase 2: Congress Members',
            'Phase 3: Congress Bills',
            'Phase 4: GovInfo Bills',
            'Phase 5: OpenStates'
        ],
        'verification': ['Phase 6: Verification']
    }

    start_time = datetime.now()
    completed_groups = []
    failed_groups = []

    for group_name, phases in parallel_groups.items():
        print(f"\n📋 Group: {group_name}")
        print(f"📜 Phases: {', '.join(phases)}")

        group_start = datetime.now()

        try:
            # Simulate parallel execution
            print(f"⚡ Starting {group_name} phases in parallel...")

            # Simulate execution time (longer groups take more time)
            if group_name == 'validation':
                time.sleep(1)
            elif group_name == 'data_ingestion':
                time.sleep(5)
            elif group_name == 'verification':
                time.sleep(2)

            group_end = datetime.now()
            duration = (group_end - group_start).total_seconds()

            completed_groups.append({
                'group': group_name,
                'phases': phases,
                'duration_seconds': duration,
                'status': 'COMPLETED'
            })

            print(f"✅ {group_name} completed in {duration:.1f}s")

        except Exception as e:
            print(f"❌ {group_name} failed: {e}")
            failed_groups.append({
                'group': group_name,
                'phases': phases,
                'error': str(e),
                'status': 'FAILED'
            })

    total_duration = (datetime.now() - start_time).total_seconds()

    # Generate demo report
    demo_report = {
        'mode': 'parallel_demo',
        'start_time': start_time.isoformat(),
        'end_time': datetime.now().isoformat(),
        'duration_seconds': total_duration,
        'total_groups': len(parallel_groups),
        'completed_groups': len(completed_groups),
        'failed_groups': len(failed_groups),
        'success_rate': (len(completed_groups) / len(parallel_groups) * 100),
        'completed_groups_details': completed_groups,
        'failed_groups_details': failed_groups,
        'overall_status': 'SUCCESS' if len(failed_groups) == 0 else 'PARTIAL_SUCCESS'
    }

    print("\n📊 Parallel Demo Results:")
    print(f"✅ Completed: {len(completed_groups)}/{len(parallel_groups)} groups")
    print(f"❌ Failed: {len(failed_groups)}/{len(parallel_groups)} groups")
    print(f"⏱️  Total Duration: {total_duration:.1f}s")
    print(f"📈 Success Rate: {demo_report['success_rate']:.1f}%")

    return demo_report

def print_menu():
    """Print the main menu"""
    print("\n" + "="*60)
    print("🚀 MULTI-AGENT INGESTION MENU")
    print("="*60)
    print("1. 📊 Validate Environment")
    print("2. 🔍 Quick Validation")
    print("3. 🔄 Sequential Orchestration")
    print("4. ⚡ Parallel Orchestration")
    print("5. 🎮 Sequential Demo")
    print("6. 🎮 Parallel Demo")
    print("7. 📋 Show Agent Configuration")
    print("8. ❌ Exit")
    print("="*60)

def show_agent_configuration():
    """Show the agent configuration"""
    print("\n📋 Agent Configuration:")
    print("="*60)

    # Create orchestrator to get default agents
    orchestrator = Orchestrator()
    default_agents = orchestrator._get_default_agents()

    for agent in default_agents:
        print(f"\n🤖 Agent: {agent.agent_id}")
        print(f"   Phase: {agent.phase_number}")
        print(f"   Script: {agent.script_path}")
        print(f"   Dependencies: {', '.join(agent.dependencies) if agent.dependencies else 'None'}")
        print(f"   Priority: {agent.priority}")
        print(f"   Timeout: {agent.timeout_seconds}s")
        print(f"   Parallel Group: {agent.parallel_group or 'Serial'}")
        print(f"   Max Retries: {agent.max_retries}")

    print("\n" + "="*60)

def interactive_mode():
    """Run in interactive mode"""
    while True:
        print_menu()

        try:
            choice = input("\n🎯 Enter your choice (1-8): ").strip()

            if choice == '1':
                validate_environment()

            elif choice == '2':
                run_quick_validation()

            elif choice == '3':
                print("\n🔄 Starting Sequential Orchestration...")
                run_orchestration("sequential", 1)

            elif choice == '4':
                print("\n⚡ Starting Parallel Orchestration...")
                max_concurrent = input("🔢 Enter max concurrent agents (default 4): ").strip()
                max_concurrent = int(max_concurrent) if max_concurrent.isdigit() else 4
                run_orchestration("parallel", max_concurrent)

            elif choice == '5':
                run_sequential_demo()

            elif choice == '6':
                run_parallel_demo()

            elif choice == '7':
                show_agent_configuration()

            elif choice == '8':
                print("\n👋 Goodbye!")
                break

            else:
                print("❌ Invalid choice. Please enter 1-8.")

            if choice != '8':
                input("\n🎯 Press Enter to continue...")

        except KeyboardInterrupt:
            print("\n\n🛑 Interrupted by user")
            break
        except Exception as e:
            print(f"\n❌ Error: {e}")
            input("\n🎯 Press Enter to continue...")

def main():
    """Main function"""
    parser = argparse.ArgumentParser(description='Run Orchestrated Multi-Agent Ingestion')
    parser.add_argument('--mode', '-m', choices=['sequential', 'parallel', 'demo-sequential', 'demo-parallel', 'interactive'],
                       default='interactive', help='Orchestration mode')
    parser.add_argument('--max-concurrent', '-c', type=int, default=4,
                       help='Maximum concurrent agents (parallel mode only)')
    parser.add_argument('--validate', action='store_true', help='Validate environment before starting')
    parser.add_argument('--quick-validate', action='store_true', help='Run quick validation only')
    parser.add_argument('--save-report', action='store_true', default=True, help='Save orchestration report')
    parser.add_argument('--output', '-o', help='Output filename for report')

    args = parser.parse_args()

    # Print banner
    print_banner()

    # Handle different modes
    if args.mode == 'interactive':
        interactive_mode()

    elif args.mode == 'demo-sequential':
        run_sequential_demo()

    elif args.mode == 'demo-parallel':
        run_parallel_demo()

    elif args.quick_validate:
        run_quick_validation()

    else:
        # Real orchestration modes
        if args.validate and not validate_environment():
            print("❌ Environment validation failed. Exiting.")
            sys.exit(1)

        if args.quick_validate and not run_quick_validation():
            print("❌ Quick validation failed. Exiting.")
            sys.exit(1)

        try:
            report = run_orchestration(args.mode, args.max_concurrent, args.save_report)

            # Exit with appropriate code
            if report['overall_status'] == 'SUCCESS':
                print("\n🎉 Orchestration completed successfully!")
                sys.exit(0)
            else:
                print("\n⚠️  Orchestration completed with issues.")
                sys.exit(1)

        except KeyboardInterrupt:
            print("\n\n🛑 Orchestration interrupted by user")
            sys.exit(130)
        except Exception as e:
            print(f"\n❌ Orchestration failed: {e}")
            sys.exit(1)

if __name__ == "__main__":
    main()
