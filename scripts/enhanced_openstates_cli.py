#!/usr/bin/env python3
"""
Enhanced OpenStates CLI
Professional command-line interface for comprehensive OpenStates data ingestion
"""

import json
import logging
import os
import sys
from datetime import datetime
from typing import Any, Dict

import click

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from openstates_orchestrator import OpenStatesOrchestrator

# ============================================================================
# CLI CONFIGURATION
# ============================================================================

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


# ============================================================================
# CLI COMMANDS
# ============================================================================

@click.group()
@click.version_option(version='1.0.0', prog_name='enhanced-openstates-cli')
@click.option('--verbose', '-v', is_flag=True, help='Enable verbose logging')
@click.option('--log-file', help='Log to file instead of console')
def cli(verbose, log_file):
    """Enhanced OpenStates CLI - Comprehensive data ingestion system"""

    if verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    if log_file:
        file_handler = logging.FileHandler(log_file)
        file_handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
        logging.getLogger().addHandler(file_handler)


@cli.command()
@click.option('--jurisdiction', '-j', help='Specific jurisdiction to ingest (e.g., ca, tx, ny)')
@click.option('--parallel', '-p', is_flag=True, help='Enable parallel processing')
@click.option('--include-details', '-d', is_flag=True, help='Include detailed enrichment')
@click.option('--data-types', '-t', help='Comma-separated data types (people,bills,committees,events)')
@click.option('--session', '-s', help='Specific legislative session')
@click.option('--batch-size', '-b', default=200, help='Batch size for API requests (max 200)')
@click.option('--max-retries', default=3, help='Maximum retry attempts')
@click.option('--timeout', default=300, help='Timeout in seconds')
@click.option('--dry-run', is_flag=True, help='Show what would be ingested without actually ingesting')
def ingest(jurisdiction, parallel, include_details, data_types, session, batch_size, max_retries, timeout, dry_run):
    """Enhanced ingestion with comprehensive data types and options"""

    click.echo("🚀 Enhanced OpenStates Ingestion")
    click.echo("=" * 40)

    try:
        # Initialize orchestrator
        orchestrator = OpenStatesOrchestrator()

        # Parse data types
        data_type_list = data_types.split(',') if data_types else ['people', 'bills', 'committees', 'events']
        data_type_list = [dt.strip() for dt in data_type_list]

        click.echo("📋 Configuration:")
        click.echo(f"   Jurisdiction: {jurisdiction or 'All'}")
        click.echo(f"   Data types: {', '.join(data_type_list)}")
        click.echo(f"   Session: {session or 'All'}")
        click.echo(f"   Parallel: {parallel}")
        click.echo(f"   Include details: {include_details}")
        click.echo(f"   Batch size: {batch_size}")
        click.echo(f"   Max retries: {max_retries}")
        click.echo(f"   Timeout: {timeout}s")
        click.echo(f"   Dry run: {dry_run}")

        if dry_run:
            click.echo("\n🔍 Dry run mode - showing what would be ingested:")

            # Show available plans
            plans = orchestrator.get_available_plans()

            if jurisdiction:
                # Show state-specific plan
                state_plan = jurisdiction.lower()
                if state_plan in plans:
                    plan = plans[state_plan]
                    click.echo(f"\n📋 Plan: {plan.name}")
                    click.echo(f"   Data types: {', '.join(plan.data_types)}")
                    click.echo(f"   Jurisdictions: {', '.join(plan.jurisdictions)}")
                    click.echo(f"   Dependencies: {', '.join(plan.dependencies)}")
                    click.echo(f"   Parallel safe: {plan.parallel_safe}")
                    click.echo(f"   Priority: {plan.priority}")
                else:
                    click.echo(f"\n📋 Ad-hoc ingestion for jurisdiction: {jurisdiction}")
                    click.echo(f"   Data types: {', '.join(data_type_list)}")
            else:
                # Show available plans
                click.echo(f"\n📋 Available plans ({len(plans)}):")
                for plan_name, plan in sorted(plans.items(), key=lambda x: x[1].priority):
                    status = "✅" if plan.parallel_safe else "🔒"
                    click.echo(f"   {status} {plan_name}: {', '.join(plan.data_types)}")

            return

        # Execute ingestion
        start_time = datetime.now()

        if jurisdiction:
            # Single jurisdiction ingestion
            click.echo(f"\n📍 Starting ingestion for jurisdiction: {jurisdiction}")
            result = orchestrator.execute_state_ingestion(jurisdiction, include_details=include_details)

            display_ingestion_result(result)

        else:
            # Comprehensive ingestion
            click.echo("\n📍 Starting comprehensive ingestion")

            # Build regions list
            regions = ['northeast_states', 'southeast_states', 'midwest_states', 'west_states', 'southwest_states']

            result = orchestrator.execute_comprehensive_ingestion(
                regions=regions,
                parallel=parallel
            )

            display_comprehensive_result(result)

        duration = (datetime.now() - start_time).total_seconds()
        click.echo(f"\n⏱️  Total duration: {duration:.1f} seconds")

    except Exception as e:
        click.echo(f"❌ Error: {e}")
        logger.error(f"Ingestion failed: {e}", exc_info=True)
        sys.exit(1)


@cli.command()
@click.option('--data-type', '-t', help='Specific data type to resume (people,bills,committees,events)')
@click.option('--jurisdiction', '-j', help='Specific jurisdiction to resume')
@click.option('--plan', '-p', help='Specific plan to resume')
@click.option('--from-checkpoint', is_flag=True, help='Resume from last checkpoint')
@click.option('--force', is_flag=True, help='Force resume even if completed')
def resume(data_type, jurisdiction, plan, from_checkpoint, force):
    """Resume interrupted ingestion from checkpoint"""

    click.echo("🔄 Resume OpenStates Ingestion")
    click.echo("=" * 35)

    try:
        orchestrator = OpenStatesOrchestrator()

        click.echo("📋 Resume configuration:")
        click.echo(f"   Data type: {data_type or 'All'}")
        click.echo(f"   Jurisdiction: {jurisdiction or 'All'}")
        click.echo(f"   Plan: {plan or 'Auto-detect'}")
        click.echo(f"   From checkpoint: {from_checkpoint}")
        click.echo(f"   Force: {force}")

        # Check checkpoint status
        if from_checkpoint:
            click.echo("\n🔍 Checking checkpoint status...")

            # Get plan status
            if plan:
                plan_status = orchestrator.get_plan_status(plan)
                click.echo(f"   Plan {plan}: {plan_status['status']}")

                if plan_status['status'] == 'completed' and not force:
                    click.echo(f"✅ Plan {plan} already completed. Use --force to re-run.")
                    return
            else:
                # Show all plan statuses
                plans = orchestrator.get_available_plans()
                click.echo("\n📋 Plan statuses:")
                for plan_name in sorted(plans.keys()):
                    status = orchestrator.get_plan_status(plan_name)
                    status_icon = "✅" if status['status'] == 'completed' else "🔄" if status['status'] == 'pending' else "❌"
                    click.echo(f"   {status_icon} {plan_name}: {status['status']}")

        # Execute resume
        start_time = datetime.now()

        if plan:
            click.echo(f"\n📍 Resuming plan: {plan}")
            result = orchestrator.execute_plan(plan)
            display_ingestion_result(result)

        elif jurisdiction:
            click.echo(f"\n📍 Resuming jurisdiction: {jurisdiction}")
            result = orchestrator.execute_state_ingestion(jurisdiction, include_details=True)
            display_ingestion_result(result)

        else:
            click.echo("\n📍 Resuming comprehensive ingestion")
            result = orchestrator.execute_comprehensive_ingestion(parallel=True)
            display_comprehensive_result(result)

        duration = (datetime.now() - start_time).total_seconds()
        click.echo(f"\n⏱️  Resume duration: {duration:.1f} seconds")

    except Exception as e:
        click.echo(f"❌ Error: {e}")
        logger.error(f"Resume failed: {e}", exc_info=True)
        sys.exit(1)


@cli.command()
@click.option('--plan', '-p', help='Specific plan to check')
@click.option('--jurisdiction', '-j', help='Specific jurisdiction to check')
@click.option('--data-type', '-t', help='Specific data type to check')
@click.option('--detailed', '-d', is_flag=True, help='Show detailed status')
def status(plan, jurisdiction, data_type, detailed):
    """Check ingestion status and progress"""

    click.echo("📊 OpenStates Ingestion Status")
    click.echo("=" * 35)

    try:
        orchestrator = OpenStatesOrchestrator()

        if plan:
            # Check specific plan status
            plan_status = orchestrator.get_plan_status(plan)
            click.echo(f"\n📋 Plan: {plan}")
            click.echo(f"   Status: {plan_status['status']}")
            click.echo(f"   Dependencies satisfied: {plan_status['dependencies_satisfied']}")
            click.echo(f"   Executed count: {plan_status['executed_count']}")
            click.echo(f"   Failed count: {plan_status['failed_count']}")

            if plan_status['last_execution']:
                exec_result = plan_status['last_execution']
                click.echo(f"   Last execution: {exec_result.start_time}")
                click.echo(f"   Records processed: {exec_result.records_processed}")
                click.echo(f"   Duration: {exec_result.duration_seconds:.1f}s")

            if plan_status['last_failure']:
                fail_result = plan_status['last_failure']
                click.echo(f"   Last failure: {fail_result.start_time}")
                click.echo(f"   Error: {fail_result.error}")

        else:
            # Show overall statistics
            stats = orchestrator.get_orchestration_statistics()
            click.echo("\n📊 Overall Statistics:")
            click.echo(f"   Start time: {stats['start_time']}")
            click.echo(f"   Duration: {stats['duration_seconds']:.1f}s")
            click.echo(f"   Plans executed: {stats['total_plans_executed']}")
            click.echo(f"   Plans failed: {stats['total_plans_failed']}")
            click.echo(f"   Total records: {stats['total_records_processed']:,}")
            click.echo(f"   Success rate: {stats['success_rate']:.1f}%")
            click.echo(f"   Records/second: {stats['records_per_second']:.1f}")

            if detailed:
                click.echo("\n📋 Detailed Plan Status:")
                plans = orchestrator.get_available_plans()
                for plan_name in sorted(plans.keys(), key=lambda x: plans[x].priority):
                    status = orchestrator.get_plan_status(plan_name)
                    status_icon = "✅" if status['status'] == 'completed' else "🔄" if status['status'] == 'pending' else "❌"

                    click.echo(f"   {status_icon} {plan_name}:")
                    click.echo(f"      Priority: {plans[plan_name].priority}")
                    click.echo(f"      Data types: {', '.join(plans[plan_name].data_types)}")
                    click.echo(f"      Dependencies: {', '.join(plans[plan_name].dependencies)}")
                    click.echo(f"      Parallel safe: {plans[plan_name].parallel_safe}")

                    if status['last_execution']:
                        click.echo(f"      Last: {status['last_execution'].records_processed} records, {status['last_execution'].duration_seconds:.1f}s")

    except Exception as e:
        click.echo(f"❌ Error: {e}")
        logger.error(f"Status check failed: {e}", exc_info=True)
        sys.exit(1)


@cli.command()
@click.option('--format', '-f', type=click.Choice(['table', 'json', 'csv']), default='table', help='Output format')
@click.option('--output', '-o', help='Output file (default: stdout)')
@click.option('--filter', help='Filter plans by name pattern')
def plans(format, output, filter):
    """List available ingestion plans"""

    click.echo("📋 Available Ingestion Plans")
    click.echo("=" * 35)

    try:
        orchestrator = OpenStatesOrchestrator()
        available_plans = orchestrator.get_available_plans()

        # Apply filter if specified
        if filter:
            available_plans = {k: v for k, v in available_plans.items() if filter.lower() in k.lower()}

        if format == 'table':
            click.echo(f"\n{'Plan Name':<25} {'Priority':<8} {'Parallel':<8} {'Data Types':<20}")
            click.echo("-" * 65)

            for plan_name, plan in sorted(available_plans.items(), key=lambda x: x[1].priority):
                parallel_icon = "✅" if plan.parallel_safe else "🔒"
                data_types_str = ', '.join(plan.data_types[:2])
                if len(plan.data_types) > 2:
                    data_types_str += f" +{len(plan.data_types)-2}"

                click.echo(f"{plan_name:<25} {plan.priority:<8} {parallel_icon:<8} {data_types_str:<20}")

        elif format == 'json':
            plans_data = {}
            for plan_name, plan in available_plans.items():
                plans_data[plan_name] = {
                    'name': plan.name,
                    'data_types': plan.data_types,
                    'jurisdictions': plan.jurisdictions,
                    'dependencies': plan.dependencies,
                    'parallel_safe': plan.parallel_safe,
                    'priority': plan.priority,
                    'timeout_minutes': plan.timeout_minutes
                }

            json_output = json.dumps(plans_data, indent=2, default=str)

            if output:
                with open(output, 'w') as f:
                    f.write(json_output)
                click.echo(f"✅ Plans written to {output}")
            else:
                click.echo(json_output)

        elif format == 'csv':
            csv_lines = ['Plan Name,Priority,Parallel Safe,Data Types,Jurisdictions,Dependencies']

            for plan_name, plan in sorted(available_plans.items(), key=lambda x: x[1].priority):
                csv_lines.append(f'"{plan_name}",{plan.priority},{plan.parallel_safe},"{",".join(plan.data_types)}","{",".join(plan.jurisdictions)}","{",".join(plan.dependencies)}"')

            csv_output = '\n'.join(csv_lines)

            if output:
                with open(output, 'w') as f:
                    f.write(csv_output)
                click.echo(f"✅ CSV written to {output}")
            else:
                click.echo(csv_output)

    except Exception as e:
        click.echo(f"❌ Error: {e}")
        logger.error(f"Plans listing failed: {e}", exc_info=True)
        sys.exit(1)


@cli.command()
@click.option('--jurisdiction', '-j', help='Specific jurisdiction to validate')
@click.option('--data-type', '-t', help='Specific data type to validate')
@click.option('--sample-size', default=10, help='Number of records to validate')
@click.option('--fix-errors', is_flag=True, help='Attempt to fix validation errors')
def validate(jurisdiction, data_type, sample_size, fix_errors):
    """Validate ingested data integrity"""

    click.echo("🔍 OpenStates Data Validation")
    click.echo("=" * 35)

    try:
        orchestrator = OpenStatesOrchestrator()

        click.echo("📋 Validation configuration:")
        click.echo(f"   Jurisdiction: {jurisdiction or 'All'}")
        click.echo(f"   Data type: {data_type or 'All'}")
        click.echo(f"   Sample size: {sample_size}")
        click.echo(f"   Fix errors: {fix_errors}")

        # This would implement data validation logic
        click.echo("\n🔍 Validation not yet implemented")
        click.echo(f"   Would validate {sample_size} records")

        if jurisdiction:
            click.echo(f"   Jurisdiction: {jurisdiction}")

        if data_type:
            click.echo(f"   Data type: {data_type}")

    except Exception as e:
        click.echo(f"❌ Error: {e}")
        logger.error(f"Validation failed: {e}", exc_info=True)
        sys.exit(1)


@cli.command()
@click.option('--output', '-o', help='Output file for report')
@click.option('--format', '-f', type=click.Choice(['text', 'json', 'html']), default='text', help='Report format')
@click.option('--include-details', '-d', is_flag=True, help='Include detailed statistics')
def report(output, format, include_details):
    """Generate comprehensive ingestion report"""

    click.echo("📊 OpenStates Ingestion Report")
    click.echo("=" * 35)

    try:
        orchestrator = OpenStatesOrchestrator()
        stats = orchestrator.get_orchestration_statistics()

        # Generate report content
        report_content = generate_report_content(stats, format, include_details)

        if output:
            with open(output, 'w') as f:
                f.write(report_content)
            click.echo(f"✅ Report written to {output}")
        else:
            click.echo(report_content)

    except Exception as e:
        click.echo(f"❌ Error: {e}")
        logger.error(f"Report generation failed: {e}", exc_info=True)
        sys.exit(1)


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def display_ingestion_result(result: Dict[str, Any]):
    """Display ingestion result in a formatted way"""

    click.echo("\n📊 Ingestion Results:")
    click.echo(f"   Total processed: {result.get('total_processed', 0):,}")
    click.echo(f"   Total errors: {result.get('total_errors', 0):,}")
    click.echo(f"   Success rate: {result.get('success_rate', 0):.1f}%")
    click.echo(f"   Duration: {result.get('duration', 0):.1f}s")

    if 'results' in result:
        sub_results = result['results']
        if isinstance(sub_results, dict):
            click.echo("\n📋 Detailed Results:")
            for key, value in sub_results.items():
                if isinstance(value, dict) and 'total_processed' in value:
                    click.echo(f"   {key}: {value.get('total_processed', 0):,} records")
                elif isinstance(value, dict) and 'error' in value:
                    click.echo(f"   {key}: ❌ {value['error']}")


def display_comprehensive_result(result: Dict[str, Any]):
    """Display comprehensive ingestion result"""

    click.echo("\n📊 Comprehensive Ingestion Results:")
    click.echo(f"   Regions: {', '.join(result.get('regions', []))}")
    click.echo(f"   Parallel execution: {result.get('parallel_execution', False)}")
    click.echo(f"   Total processed: {result.get('total_processed', 0):,}")
    click.echo(f"   Total errors: {result.get('total_errors', 0):,}")
    click.echo(f"   Successful plans: {result.get('successful_plans', 0)}/{result.get('total_plans', 0)}")
    click.echo(f"   Success rate: {result.get('success_rate', 0):.1f}%")
    click.echo(f"   Duration: {result.get('duration', 0):.1f}s")
    click.echo(f"   Records/second: {result.get('records_per_second', 0):.1f}")

    if 'results' in result:
        results = result['results']
        click.echo("\n📋 Phase Results:")
        for phase_name, phase_results in results.items():
            if isinstance(phase_results, dict):
                phase_processed = sum(r.get('records_processed', 0) for r in phase_results.values() if hasattr(r, 'records_processed'))
                phase_total = len(phase_results)
                click.echo(f"   {phase_name}: {phase_processed:,} records, {phase_total} plans")


def generate_report_content(stats: Dict[str, Any], format: str, include_details: bool) -> str:
    """Generate report content in specified format"""

    if format == 'json':
        return json.dumps(stats, indent=2, default=str)

    elif format == 'html':
        return f"""
<!DOCTYPE html>
<html>
<head>
    <title>OpenStates Ingestion Report</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; }}
        .header {{ background-color: #f0f0f0; padding: 20px; border-radius: 5px; }}
        .stats {{ margin: 20px 0; }}
        .stat-item {{ margin: 10px 0; }}
        .success {{ color: green; }}
        .error {{ color: red; }}
    </style>
</head>
<body>
    <div class="header">
        <h1>OpenStates Ingestion Report</h1>
        <p>Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
    </div>

    <div class="stats">
        <h2>Overall Statistics</h2>
        <div class="stat-item"><strong>Duration:</strong> {stats['duration_seconds']:.1f}s</div>
        <div class="stat-item"><strong>Plans Executed:</strong> {stats['total_plans_executed']}</div>
        <div class="stat-item"><strong>Plans Failed:</strong> {stats['total_plans_failed']}</div>
        <div class="stat-item"><strong>Total Records:</strong> {stats['total_records_processed']:,}</div>
        <div class="stat-item success><strong>Success Rate:</strong> {stats['success_rate']:.1f}%</div>
        <div class="stat-item"><strong>Records/Second:</strong> {stats['records_per_second']:.1f}</div>
    </div>
</body>
</html>
"""

    else:  # text format
        report = f"""
OpenStates Ingestion Report
Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
{'=' * 50}

Overall Statistics:
  Duration: {stats['duration_seconds']:.1f}s
  Plans Executed: {stats['total_plans_executed']}
  Plans Failed: {stats['total_plans_failed']}
  Total Records: {stats['total_records_processed']:,}
  Success Rate: {stats['success_rate']:.1f}%
  Records/Second: {stats['records_per_second']:.1f}
"""

        if include_details:
            report += "\nExecuted Plans:\n"
            for plan_name in stats.get('executed_plans', []):
                report += f"  ✅ {plan_name}\n"

            if stats.get('failed_plans'):
                report += "\nFailed Plans:\n"
                for plan_name in stats.get('failed_plans', []):
                    report += f"  ❌ {plan_name}\n"

        return report


# ============================================================================
# MAIN ENTRY POINT
# ============================================================================

if __name__ == '__main__':
    cli()
