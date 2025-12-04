#!/usr/bin/env python3
"""
OpenDiscourse CLI - Unified entry point for all tools.

Provides a single CLI with subcommands for each data source.
"""

import sys
import click
from rich.console import Console

console = Console()


@click.group()
@click.version_option(version="2.0.0")
def cli():
    """OpenDiscourse CLI - Congressional and legislative data tools."""
    pass


@cli.command()
def bootstrap():
    """Initialize database and apply migrations."""
    try:
        from scripts.core.database import bootstrap_interactive
        bootstrap_interactive()
    except ImportError as e:
        console.print(f"[red]Error:[/red] {e}")
        console.print("\n[yellow]Install dependencies:[/yellow]")
        console.print("  pip install pydantic pydantic-settings")
        sys.exit(1)


@cli.group()
def congress():
    """Congress.gov data ingestion."""
    pass


@cli.group()
def states():
    """OpenStates data ingestion."""
    pass


@cli.group()
def govinfo():
    """GovInfo data ingestion."""
    pass


# Congress commands
@congress.command('bills')
@click.argument('congress', type=int)
@click.option('--bill-type', default='all', help='Bill type filter')
@click.option('--dry-run', is_flag=True, help='Dry run without changes')
def congress_bills(congress, bill_type, dry_run):
    """Ingest bills for a congress."""
    try:
        from scripts.core.base_cli import verify_prerequisites
        if not verify_prerequisites('congress'):
            sys.exit(1)

        # Import and run actual CLI
        from scripts.ingestion.congress_cli import main as congress_main
        sys.argv = ['congress_cli.py', 'ingest-bills', str(congress)]
        if dry_run:
            sys.argv.insert(1, '--dry-run')
        congress_main()

    except ImportError as e:
        console.print(f"[red]Error:[/red] {e}")
        sys.exit(1)


@congress.command('members')
@click.argument('congress', type=int)
@click.option('--dry-run', is_flag=True, help='Dry run without changes')
def congress_members(congress, dry_run):
    """Ingest members for a congress."""
    try:
        from scripts.core.base_cli import verify_prerequisites
        if not verify_prerequisites('congress'):
            sys.exit(1)

        from scripts.ingestion.congress_cli import main as congress_main
        sys.argv = ['congress_cli.py', 'ingest-members', str(congress)]
        if dry_run:
            sys.argv.insert(1, '--dry-run')
        congress_main()

    except ImportError as e:
        console.print(f"[red]Error:[/red] {e}")
        sys.exit(1)


# OpenStates commands
@states.command('bills')
@click.argument('jurisdiction')
@click.option('--years-back', type=int, default=1, help='Years of history')
@click.option('--dry-run', is_flag=True, help='Dry run without changes')
def states_bills(jurisdiction, years_back, dry_run):
    """Ingest bills for a jurisdiction."""
    try:
        from scripts.core.base_cli import verify_prerequisites
        if not verify_prerequisites('openstates'):
            sys.exit(1)

        from scripts.ingestion.openstates_cli import main as states_main
        sys.argv = ['openstates_cli.py', 'ingest-bills', jurisdiction, '--years-back', str(years_back)]
        if dry_run:
            sys.argv.insert(1, '--dry-run')
        states_main()

    except ImportError as e:
        console.print(f"[red]Error:[/red] {e}")
        sys.exit(1)


# GovInfo commands
@govinfo.command('collections')
@click.option('--dry-run', is_flag=True, help='Dry run without changes')
def govinfo_collections(dry_run):
    """List available collections."""
    try:
        from scripts.core.base_cli import verify_prerequisites
        if not verify_prerequisites('govinfo'):
            sys.exit(1)

        from scripts.ingestion.govinfo_cli import main as govinfo_main
        sys.argv = ['govinfo_cli.py', 'list-collections']
        if dry_run:
            sys.argv.insert(1, '--dry-run')
        govinfo_main()

    except ImportError as e:
        console.print(f"[red]Error:[/red] {e}")
        sys.exit(1)


@cli.command()
def verify():
    """Verify system configuration and database setup."""
    console.print("\n[bold]OpenDiscourse System Verification[/bold]\n")

    # Check configuration
    try:
        from scripts.core.config import get_settings
        settings = get_settings()
        console.print("[green]✓[/green] Configuration system: OK")
    except ImportError:
        console.print("[red]✗[/red] Configuration system: Pydantic not installed")
        console.print("  Install: pip install pydantic pydantic-settings")
        return
    except Exception as e:
        console.print(f"[red]✗[/red] Configuration system: {e}")
        return

    # Check database
    try:
        from scripts.core.database import DatabaseBootstrap
        db = DatabaseBootstrap(settings)
        if db.test_connection():
            console.print("[green]✓[/green] Database connection: OK")
        else:
            console.print("[red]✗[/red] Database connection: Failed")
            return
    except Exception as e:
        console.print(f"[red]✗[/red] Database: {e}")
        return

    # Check API keys
    for api_name, api_config in [
        ('Congress', settings.congress_api),
        ('OpenStates', settings.openstates_api),
        ('GovInfo', settings.govinfo_api),
    ]:
        if api_config.api_key:
            console.print(f"[green]✓[/green] {api_name} API key: Configured")
        else:
            console.print(f"[yellow]⚠[/yellow] {api_name} API key: Not set")

    console.print("\n[green]✓[/green] System verification complete!\n")


if __name__ == '__main__':
    cli()
