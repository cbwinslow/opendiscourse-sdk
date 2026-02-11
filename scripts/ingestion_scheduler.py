#!/usr/bin/env python3
"""
Automated Congress Members Ingestion Scheduler
Sets up and runs scheduled ingestion tasks
"""

import argparse
import json
import logging
import os
import subprocess
import sys
import time
from datetime import datetime, timedelta
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

from dotenv import load_dotenv

load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(project_root / 'logs' / 'ingestion.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class CongressIngestionScheduler:
    """Scheduler for automated Congress data ingestion"""

    def __init__(self, config_file=None):
        self.project_root = project_root
        self.config_file = config_file or (self.project_root / 'config' / 'ingestion_config.json')
        self.config = self.load_config()
        self.ingestion_script = self.project_root / 'scripts' / 'ingest_members_official.py'
        self.verification_script = self.project_root / 'scripts' / 'verify_congress_data.py'

        # Ensure log directory exists
        log_dir = self.project_root / 'logs'
        log_dir.mkdir(exist_ok=True)

    def load_config(self):
        """Load ingestion configuration"""
        default_config = {
            "ingestion": {
                "congress_start": 101,
                "congress_end": 118,
                "batch_size": 50,
                "request_delay": 0.5,
                "max_retries": 3
            },
            "schedule": {
                "enabled": False,
                "frequency": "weekly",
                "day_of_week": "sunday",
                "time": "02:00",
                "timezone": "UTC"
            },
            "verification": {
                "enabled": True,
                "run_after_ingestion": True,
                "data_quality_threshold": 0.95
            },
            "notifications": {
                "enabled": False,
                "email": None,
                "webhook_url": None
            },
            "backup": {
                "enabled": True,
                "backup_before_ingestion": True,
                "backup_retention_days": 30
            }
        }

        if self.config_file.exists():
            try:
                with open(self.config_file) as f:
                    config = json.load(f)
                # Merge with defaults
                return {**default_config, **config}
            except Exception as e:
                logger.warning(f"Failed to load config file {self.config_file}: {e}")
                logger.info("Using default configuration")

        # Create default config file
        self.save_config(default_config)
        return default_config

    def save_config(self, config=None):
        """Save configuration to file"""
        config = config or self.config
        config_file = self.config_file

        # Ensure config directory exists
        config_file.parent.mkdir(exist_ok=True)

        with open(config_file, 'w') as f:
            json.dump(config, f, indent=2)

        logger.info(f"Configuration saved to {config_file}")

    def run_ingestion(self, congress_start=None, congress_end=None, batch_size=None):
        """Run the ingestion process"""
        config = self.config['ingestion']

        # Override with provided parameters
        congress_start = congress_start or config['congress_start']
        congress_end = congress_end or config['congress_end']
        batch_size = batch_size or config['batch_size']

        logger.info(f"Starting ingestion for Congress {congress_start}-{congress_end}")

        cmd = [
            'python', str(self.ingestion_script),
            '--congress-start', str(congress_start),
            '--congress-end', str(congress_end),
            '--batch-size', str(batch_size)
        ]

        start_time = time.time()

        try:
            result = subprocess.run(
                cmd,
                cwd=self.project_root,
                capture_output=True,
                text=True,
                timeout=3600  # 1 hour timeout
            )

            duration = time.time() - start_time

            if result.returncode == 0:
                logger.info(f"Ingestion completed successfully in {duration:.2f} seconds")

                # Parse results from output
                output_lines = result.stdout.split('\n')
                for line in output_lines:
                    if 'Total Members Processed:' in line:
                        members = line.split(':')[-1].strip()
                        logger.info(f"Members processed: {members}")
                    elif 'Total Terms Processed:' in line:
                        terms = line.split(':')[-1].strip()
                        logger.info(f"Terms processed: {terms}")
                    elif 'Total Errors:' in line:
                        errors = line.split(':')[-1].strip()
                        logger.info(f"Errors: {errors}")

                return True
            else:
                logger.error(f"Ingestion failed with return code {result.returncode}")
                logger.error(f"Error output: {result.stderr}")
                return False

        except subprocess.TimeoutExpired:
            logger.error("Ingestion timed out after 1 hour")
            return False
        except Exception as e:
            logger.error(f"Ingestion failed with exception: {e}")
            return False

    def run_verification(self):
        """Run data verification"""
        if not self.config['verification']['enabled']:
            logger.info("Verification disabled in configuration")
            return True

        logger.info("Running data verification")

        cmd = ['python', str(self.verification_script)]

        try:
            result = subprocess.run(
                cmd,
                cwd=self.project_root,
                capture_output=True,
                text=True,
                timeout=300  # 5 minute timeout
            )

            if result.returncode == 0:
                logger.info("Verification completed successfully")
                logger.info(f"Verification output: {result.stdout}")
                return True
            else:
                logger.error(f"Verification failed: {result.stderr}")
                return False

        except subprocess.TimeoutExpired:
            logger.error("Verification timed out")
            return False
        except Exception as e:
            logger.error(f"Verification failed with exception: {e}")
            return False

    def backup_database(self):
        """Create database backup before ingestion"""
        if not self.config['backup']['enabled']:
            logger.info("Database backup disabled")
            return True

        logger.info("Creating database backup")

        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_file = self.project_root / 'backups' / f'congress_backup_{timestamp}.sql'

        # Ensure backup directory exists
        backup_file.parent.mkdir(exist_ok=True)

        try:
            # Create backup using pg_dump
            cmd = [
                'pg_dump',
                '-U', os.getenv('DB_USER', 'cbwinslow'),
                '-d', os.getenv('DB_NAME', 'cbwinslow'),
                '-f', str(backup_file),
                '--schema=congress'
            ]

            result = subprocess.run(cmd, capture_output=True, text=True)

            if result.returncode == 0:
                logger.info(f"Database backup created: {backup_file}")

                # Clean up old backups
                self.cleanup_old_backups()
                return True
            else:
                logger.error(f"Database backup failed: {result.stderr}")
                return False

        except Exception as e:
            logger.error(f"Database backup failed with exception: {e}")
            return False

    def cleanup_old_backups(self):
        """Clean up old backup files"""
        backup_dir = self.project_root / 'backups'
        retention_days = self.config['backup']['backup_retention_days']

        if not backup_dir.exists():
            return

        cutoff_date = datetime.now() - timedelta(days=retention_days)

        for backup_file in backup_dir.glob('congress_backup_*.sql'):
            try:
                # Extract timestamp from filename
                timestamp_str = backup_file.stem.split('_')[-1]
                file_date = datetime.strptime(timestamp_str, '%Y%m%d_%H%M%S')

                if file_date < cutoff_date:
                    backup_file.unlink()
                    logger.info(f"Deleted old backup: {backup_file}")

            except Exception as e:
                logger.warning(f"Failed to process backup file {backup_file}: {e}")

    def send_notification(self, message, success=True):
        """Send notification about ingestion results"""
        if not self.config['notifications']['enabled']:
            return

        # Implementation would depend on notification method
        logger.info(f"Notification: {message}")

    def run_full_ingestion(self, congress_start=None, congress_end=None):
        """Run complete ingestion process with backup and verification"""
        logger.info("Starting full ingestion process")

        # Step 1: Backup database
        if self.config['backup']['backup_before_ingestion']:
            if not self.backup_database():
                logger.error("Database backup failed, aborting ingestion")
                return False

        # Step 2: Run ingestion
        ingestion_success = self.run_ingestion(congress_start, congress_end)

        if not ingestion_success:
            self.send_notification("Ingestion failed", False)
            return False

        # Step 3: Run verification
        if self.config['verification']['run_after_ingestion']:
            verification_success = self.run_verification()

            if not verification_success:
                self.send_notification("Ingestion completed but verification failed", False)
                return False

        self.send_notification("Ingestion completed successfully", True)
        return True

    def setup_cron_job(self):
        """Set up cron job for scheduled ingestion"""
        if not self.config['schedule']['enabled']:
            logger.info("Scheduled ingestion disabled")
            return

        schedule_config = self.config['schedule']

        # Build cron schedule
        if schedule_config['frequency'] == 'weekly':
            day_map = {
                'sunday': 0, 'monday': 1, 'tuesday': 2, 'wednesday': 3,
                'thursday': 4, 'friday': 5, 'saturday': 6
            }
            day_of_week = day_map.get(schedule_config['day_of_week'].lower(), 0)
            time_parts = schedule_config['time'].split(':')
            hour = int(time_parts[0])
            minute = int(time_parts[1]) if len(time_parts) > 1 else 0

            cron_schedule = f"{minute} {hour} * * {day_of_week}"
        else:
            # Default to daily at 2 AM
            cron_schedule = "0 2 * * *"

        # Build cron command
        python_path = sys.executable
        scheduler_path = __file__
        log_path = self.project_root / 'logs' / 'cron_ingestion.log'

        cron_command = f"{cron_schedule} {python_path} {scheduler_path} --auto >> {log_path} 2>&1"

        logger.info(f"Cron command: {cron_command}")
        logger.info("To set up cron job, run:")
        logger.info("crontab -e")
        logger.info("Add this line:")
        logger.info(cron_command)

    def run_scheduled_ingestion(self):
        """Run ingestion as scheduled task"""
        logger.info("Running scheduled ingestion")

        success = self.run_full_ingestion()

        if success:
            logger.info("Scheduled ingestion completed successfully")
        else:
            logger.error("Scheduled ingestion failed")

        return success


def main():
    """Main function"""
    parser = argparse.ArgumentParser(description="Congress Members Ingestion Scheduler")
    parser.add_argument('--config', type=str, help='Configuration file path')
    parser.add_argument('--congress-start', type=int, help='Starting congress number')
    parser.add_argument('--congress-end', type=int, help='Ending congress number')
    parser.add_argument('--batch-size', type=int, help='Batch size for API requests')
    parser.add_argument('--verify-only', action='store_true', help='Run verification only')
    parser.add_argument('--backup-only', action='store_true', help='Create backup only')
    parser.add_argument('--setup-cron', action='store_true', help='Set up cron job')
    parser.add_argument('--auto', action='store_true', help='Run as scheduled task')

    args = parser.parse_args()

    # Initialize scheduler
    scheduler = CongressIngestionScheduler(args.config)

    if args.setup_cron:
        scheduler.setup_cron_job()
        return

    if args.backup_only:
        scheduler.backup_database()
        return

    if args.verify_only:
        scheduler.run_verification()
        return

    if args.auto:
        scheduler.run_scheduled_ingestion()
        return

    # Run full ingestion
    success = scheduler.run_full_ingestion(
        congress_start=args.congress_start,
        congress_end=args.congress_end
    )

    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()