"""
Main CLI interface for Congress CLI.
"""

import json
import sys

import click
from rich.console import Console
from rich.progress import (
    BarColumn,
    Progress,
    SpinnerColumn,
    TextColumn,
    TimeRemainingColumn,
)
from rich.table import Table

from .database.migrations import DatabaseBootstrap, DatabaseManager
from .ingestion.incremental import IncrementalIngestor
from .utils.config import get_config
from .utils.logger import setup_logging

# Initialize rich console
console = Console()


@click.group()
@click.option('--verbose', '-v', is_flag=True, help='Enable verbose logging')
@click.option('--config', '-c', type=click.Path(exists=True), help='Configuration file path')
@click.option('--database-url', help='Database connection URL')
@click.option('--api-key', help='Congress.gov API key')
@click.pass_context
def cli(ctx, verbose, config, database_url, api_key):
    """Congress CLI - Bulk data ingestion tool for Congress.gov

    A comprehensive tool for ingesting bulk data from Congress.gov with:
    • SQL database bootstrap and migration
    • Incremental ingestion with offset tracking
    • Real-time monitoring and progress tracking
    • Sophisticated error handling and retry logic
    • Pydantic models for data validation
    """
    ctx.ensure_object(dict)
    ctx.obj['verbose'] = verbose
    ctx.obj['config'] = config
    ctx.obj['database_url'] = database_url
    ctx.obj['api_key'] = api_key

    # Setup logging
    setup_logging(verbose)

    # Load configuration
    try:
        config_obj = get_config(config)
        if database_url:
            config_obj.database_url = database_url
        if api_key:
            config_obj.api_key = api_key
        ctx.obj['config_obj'] = config_obj
    except Exception as e:
        console.print(f"[red]Configuration error: {e}[/red]")
        sys.exit(1)


@cli.command()
@click.option('--drop-existing', is_flag=True, help='Drop existing tables before creating new ones')
@click.option('--dry-run', is_flag=True, help='Show what would be done without executing')
@click.pass_context
def bootstrap(ctx, drop_existing, dry_run):
    """Bootstrap database with Congress schema and tables."""
    console.print("[bold blue]🚀 Database Bootstrap[/bold blue]")

    config = ctx.obj['config_obj']

    if dry_run:
        console.print("[yellow]DRY RUN MODE - No changes will be made[/yellow]")

        # Show what would be done
        bootstrap = DatabaseBootstrap(config.database_url)
        status = bootstrap.get_migration_status()

        console.print("\n[bold]Migration Status:[/bold]")
        console.print(f"  Schemas: {', '.join(status.get('schemas', []))}")
        console.print(f"  Migration files: {status.get('migration_files', 0)}")
        console.print(f"  Status: {status.get('status', 'unknown')}")

        if drop_existing:
            console.print("\n[yellow]Would drop existing schemas and tables:[/yellow]")
            console.print("  • congress schema")
            console.print("  • incremental schema")
            console.print("  • All tables and data")

        return

    try:
        bootstrap = DatabaseBootstrap(config.database_url)

        with console.status("[bold green]Bootstrapping database..."):
            success = bootstrap.bootstrap_database(drop_existing)

        if success:
            console.print("[green]✅ Database bootstrap completed successfully[/green]")

            # Show status
            status = bootstrap.get_migration_status()
            console.print("\n[bold]Bootstrap Status:[/bold]")
            console.print(f"  Schemas created: {', '.join(status.get('schemas', []))}")

            for schema, count in status.get('table_counts', {}).items():
                console.print(f"  {schema} tables: {count}")
        else:
            console.print("[red]❌ Database bootstrap failed[/red]")
            sys.exit(1)

    except Exception as e:
        console.print(f"[red]❌ Bootstrap error: {e}[/red]")
        sys.exit(1)


@cli.command()
@click.option('--congress', default=118, help='Congress number to ingest (default: 118)')
@click.option('--resume', is_flag=True, default=True, help='Resume from checkpoint if available')
@click.option('--batch-size', default=100, help='Batch size for processing (default: 100)')
@click.option('--max-workers', default=4, help='Maximum parallel workers (default: 4)')
@click.option('--dry-run', is_flag=True, help='Show ingestion plan without executing')
@click.pass_context
def ingest_members(ctx, congress, resume, batch_size, max_workers, dry_run):
    """Ingest Congress members data for specified Congress."""
    console.print(f"[bold blue]👥 Ingesting Congress {congress} Members[/bold blue]")

    config = ctx.obj['config_obj']

    if dry_run:
        console.print("[yellow]DRY RUN MODE - No data will be ingested[/yellow]")

        # Show ingestion plan
        console.print("\n[bold]Ingestion Plan:[/bold]")
        console.print(f"  Congress: {congress}")
        console.print("  Data type: Members")
        console.print(f"  Resume from checkpoint: {resume}")
        console.print(f"  Batch size: {batch_size}")
        console.print(f"  Max workers: {max_workers}")
        console.print(f"  API endpoint: {config.api.base_url}/member/congress/{congress}")

        # Check checkpoint status
        try:
            ingestor = IncrementalIngestor(config)
            checkpoint = ingestor.get_checkpoint('congress', 'members', str(congress))

            if checkpoint:
                console.print("\n[bold]Checkpoint Status:[/bold]")
                console.print(f"  Offset: {checkpoint.offset}")
                console.print(f"  Total processed: {checkpoint.total_processed}")
                console.print(f"  Status: {checkpoint.status}")
                console.print(f"  Last ingestion: {checkpoint.last_ingestion_at}")
            else:
                console.print("\n[yellow]No existing checkpoint found - will start from beginning[/yellow]")
        except Exception as e:
            console.print(f"[yellow]Could not check checkpoint status: {e}[/yellow]")

        return

    try:
        ingestor = IncrementalIngestor(config)
        ingestor.batch_size = batch_size
        ingestor.max_workers = max_workers

        # Setup rich progress display
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TextColumn("{task.percentage:>3.0f}%"),
            TimeRemainingColumn(),
            console=console
        ) as progress:

            task = progress.add_task("Ingesting members...", total=None)

            def progress_callback(processed: int, total: int, expected: int):
                progress.update(task, completed=processed, total=expected)

            # Run ingestion
            result = ingestor.ingest_members(congress, resume, progress_callback)

            progress.update(task, completed=result['total_processed'], total=result['total_expected'])

        # Display results
        console.print("\n[bold green]✅ Members Ingestion Completed[/bold green]")
        console.print(f"  Total processed: {result['total_processed']:,}")
        console.print(f"  Total expected: {result['total_expected']:,}")
        console.print(f"  Completion: {result['completion_percentage']:.1f}%")
        console.print(f"  Duration: {result['duration_seconds']:.1f} seconds")
        console.print(f"  Rate: {result['items_per_second']:.1f} members/second")

        if result['failed_items'] > 0:
            console.print(f"[yellow]  Failed items: {result['failed_items']}[/yellow]")

    except KeyboardInterrupt:
        console.print("\n[yellow]⚠️  Ingestion interrupted by user[/yellow]")
        sys.exit(130)
    except Exception as e:
        console.print(f"[red]❌ Members ingestion failed: {e}[/red]")
        sys.exit(1)


@cli.command()
@click.option('--congress', default=118, help='Congress number to ingest (default: 118)')
@click.option('--resume', is_flag=True, default=True, help='Resume from checkpoint if available')
@click.option('--batch-size', default=100, help='Batch size for processing (default: 100)')
@click.option('--max-workers', default=4, help='Maximum parallel workers (default: 4)')
@click.option('--dry-run', is_flag=True, help='Show ingestion plan without executing')
@click.pass_context
def ingest_bills(ctx, congress, resume, batch_size, max_workers, dry_run):
    """Ingest Congress bills data for specified Congress."""
    console.print(f"[bold blue]📜 Ingesting Congress {congress} Bills[/bold blue]")

    config = ctx.obj['config_obj']

    if dry_run:
        console.print("[yellow]DRY RUN MODE - No data will be ingested[/yellow]")

        # Show ingestion plan
        console.print("\n[bold]Ingestion Plan:[/bold]")
        console.print(f"  Congress: {congress}")
        console.print("  Data type: Bills")
        console.print(f"  Resume from checkpoint: {resume}")
        console.print(f"  Batch size: {batch_size}")
        console.print(f"  Max workers: {max_workers}")
        console.print(f"  API endpoint: {config.api.base_url}/bill/congress/{congress}")

        return

    try:
        ingestor = IncrementalIngestor(config)
        ingestor.batch_size = batch_size
        ingestor.max_workers = max_workers

        # Setup rich progress display
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TextColumn("{task.percentage:>3.0f}%"),
            TimeRemainingColumn(),
            console=console
        ) as progress:

            task = progress.add_task("Ingesting bills...", total=None)

            def progress_callback(processed: int, total: int, expected: int):
                progress.update(task, completed=processed, total=expected)

            # Run ingestion
            result = ingestor.ingest_bills(congress, resume, progress_callback)

            progress.update(task, completed=result['total_processed'], total=result['total_expected'])

        # Display results
        console.print("\n[bold green]✅ Bills Ingestion Completed[/bold green]")
        console.print(f"  Total processed: {result['total_processed']:,}")
        console.print(f"  Total expected: {result['total_expected']:,}")
        console.print(f"  Completion: {result['completion_percentage']:.1f}%")
        console.print(f"  Duration: {result['duration_seconds']:.1f} seconds")
        console.print(f"  Rate: {result['items_per_second']:.1f} bills/second")

        if result['failed_items'] > 0:
            console.print(f"[yellow]  Failed items: {result['failed_items']}[/yellow]")

    except KeyboardInterrupt:
        console.print("\n[yellow]⚠️  Ingestion interrupted by user[/yellow]")
        sys.exit(130)
    except Exception as e:
        console.print(f"[red]❌ Bills ingestion failed: {e}[/red]")
        sys.exit(1)


@cli.command()
@click.pass_context
def status(ctx):
    """Show ingestion status and checkpoints."""
    console.print("[bold blue]📊 Ingestion Status[/bold blue]")

    config = ctx.obj['config_obj']

    try:
        ingestor = IncrementalIngestor(config)

        # Get all checkpoints
        checkpoints = ingestor.get_all_checkpoints()

        if not checkpoints:
            console.print("[yellow]No ingestion checkpoints found[/yellow]")
            return

        # Create status table
        table = Table(title="Ingestion Checkpoints")
        table.add_column("Data Source", style="cyan")
        table.add_column("Data Type", style="magenta")
        table.add_column("Category", style="green")
        table.add_column("Status", style="yellow")
        table.add_column("Processed", justify="right")
        table.add_column("Offset", justify="right")
        table.add_column("Last Updated")

        for checkpoint in checkpoints:
            status_style = "green" if checkpoint.status == "completed" else "yellow" if checkpoint.status == "active" else "red"
            table.add_row(
                checkpoint.data_source,
                checkpoint.data_type,
                checkpoint.category or "N/A",
                f"[{status_style}]{checkpoint.status}[/{status_style}]",
                f"{checkpoint.total_processed:,}",
                checkpoint.offset,
                checkpoint.updated_at.strftime("%Y-%m-%d %H:%M") if checkpoint.updated_at else "Never"
            )

        console.print(table)

    except Exception as e:
        console.print(f"[red]❌ Failed to get status: {e}[/red]")


@cli.command()
@click.pass_context
def info(ctx):
    """Show database and configuration information."""
    console.print("[bold blue]ℹ️  System Information[/bold blue]")

    config = ctx.obj['config_obj']

    try:
        # Database information
        db_manager = DatabaseManager(config.database_url)
        db_info = db_manager.get_database_info()

        console.print("\n[bold]Database Information:[/bold]")
        console.print(f"  Status: {db_info.get('status', 'unknown')}")
        console.print(f"  Size: {db_info.get('size', 'unknown')}")

        for schema, count in db_info.get('table_counts', {}).items():
            console.print(f"  {schema} tables: {count}")

        # Configuration information
        console.print("\n[bold]Configuration:[/bold]")
        console.print(f"  API Base URL: {config.api.base_url}")
        console.print(f"  Rate Limit: {config.api.rate_limit_per_second} requests/sec")
        console.print(f"  Timeout: {config.api.timeout_seconds} seconds")
        console.print(f"  Max Retries: {config.api.max_retries}")
        console.print(f"  Batch Size: {config.batch_size}")
        console.print(f"  Max Workers: {config.max_workers}")

        # API key status (masked)
        api_key_status = "✅ Set" if config.api.api_key else "❌ Not set"
        console.print(f"  API Key: {api_key_status}")

    except Exception as e:
        console.print(f"[red]❌ Failed to get information: {e}[/red]")


@cli.command()
@click.option('--days', default=7, help='Number of days to include in report (default: 7)')
@click.option('--output', '-o', type=click.Path(), help='Output file for report (JSON format)')
@click.pass_context
def report(ctx, days, output):
    """Generate comprehensive ingestion report."""
    console.print(f"[bold blue]📈 Generating Report (Last {days} Days)[/bold blue]")

    config = ctx.obj['config_obj']

    try:
        ingestor = IncrementalIngestor(config)

        # Generate report
        report_data = ingestor.generate_report(days)

        # Display summary
        console.print("\n[bold]Report Summary:[/bold]")
        console.print(f"  Report Period: {report_data['period']['start']} to {report_data['period']['end']}")
        console.print(f"  Total Data Sources: {len(report_data['data_sources'])}")
        console.print(f"  Total Checkpoints: {report_data['summary']['total_checkpoints']}")
        console.print(f"  Total Records Processed: {report_data['summary']['total_processed']:,}")
        console.print(f"  Total Errors: {report_data['summary']['total_errors']}")

        # Data source details
        for source in report_data['data_sources']:
            console.print(f"\n[bold]{source['name']}:[/bold]")
            console.print(f"  Checkpoints: {source['checkpoint_count']}")
            console.print(f"  Records Processed: {source['total_processed']:,}")
            console.print(f"  Success Rate: {source['success_rate']:.1f}%")
            console.print(f"  Avg Processing Rate: {source['avg_rate']:.1f} records/sec")

        # Save to file if requested
        if output:
            with open(output, 'w') as f:
                json.dump(report_data, f, indent=2, default=str)
            console.print(f"\n[green]✅ Report saved to: {output}[/green]")

    except Exception as e:
        console.print(f"[red]❌ Failed to generate report: {e}[/red]")
        sys.exit(1)


@cli.command()
@click.pass_context
def test_connection(ctx):
    """Test database and API connections."""
    console.print("[bold blue]🔧 Testing Connections[/bold blue]")

    config = ctx.obj['config_obj']

    # Test database connection
    console.print("Testing database connection...")
    try:
        db_manager = DatabaseManager(config.database_url)
        db_success = db_manager.test_connection()

        if db_success:
            console.print("[green]✅ Database connection successful[/green]")
        else:
            console.print("[red]❌ Database connection failed[/red]")
    except Exception as e:
        console.print(f"[red]❌ Database connection error: {e}[/red]")

    # Test API connection
    console.print("\nTesting API connection...")
    try:
        from .api.client import CongressAPIClient

        client = CongressAPIClient(config.api.api_key, config.api)
        api_success = client.test_connection()

        if api_success:
            console.print("[green]✅ API connection successful[/green]")

            # Show API statistics
            stats = client.get_api_statistics()
            console.print(f"  Rate Limit: {stats['rate_limit']} requests/sec")
            console.print(f"  Timeout: {config.api.timeout_seconds} seconds")
        else:
            console.print("[red]❌ API connection failed[/red]")

        client.close()
    except Exception as e:
        console.print(f"[red]❌ API connection error: {e}[/red]")


@cli.command()
@click.pass_context
def version(ctx):
    """Show version information."""
    from . import __author__, __email__, __version__

    console.print("[bold blue]📦 Congress CLI[/bold blue]")
    console.print(f"  Version: {__version__}")
    console.print(f"  Author: {__author__}")
    console.print(f"  Email: {__email__}")
    console.print(f"  Python: {sys.version}")


def main():
    """Main entry point."""
    cli()


if __name__ == '__main__':
    main()
