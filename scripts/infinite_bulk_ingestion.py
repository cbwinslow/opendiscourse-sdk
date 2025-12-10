#!/usr/bin/env python3
"""
Infinite Loop Bulk Data Ingestion System
Continuously processes ingestion commands with thread management,
maintaining maximum throughput while handling data over a 20-year span.
"""

import os
import sys
import json
import time
import logging
import argparse
import subprocess
import threading
import queue
import signal
import traceback
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed, Future
from functools import wraps
from collections import defaultdict, deque
import requests
import yaml

# Add project root to path
sys.path.append(str(Path(__file__).parent.parent))

# Configure comprehensive logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/infinite_bulk_ingestion.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

class CommandQueueManager:
    """Manages a queue of commands to be executed with thread control"""

    def __init__(self, max_threads: int = 10):
        self.max_threads = max_threads
        self.active_threads = 0
        self.command_queue = queue.PriorityQueue()
        self.running_commands = {}
        self.completed_commands = []
        self.failed_commands = []
        self.command_counter = 0
        self.lock = threading.Lock()
        self.running = True

        # Statistics
        self.stats = {
            'total_commands': 0,
            'completed_commands': 0,
            'failed_commands': 0,
            'total_records': 0,
            'start_time': time.time(),
            'last_activity': time.time()
        }

    def add_command(self, command: str, priority: int = 1, retry_count: int = 0):
        """Add a command to the queue with priority and retry tracking"""
        with self.lock:
            self.command_counter += 1
            command_id = f"cmd_{self.command_counter:06d}"

            queue_item = {
                'id': command_id,
                'command': command,
                'priority': priority,
                'retry_count': retry_count,
                'created_at': time.time(),
                'status': 'pending'
            }

            self.command_queue.put((priority, command_id, queue_item))
            self.stats['total_commands'] += 1

            logger.debug(f"📋 Added command {command_id}: {command[:100]}...")
            return command_id

    def get_next_command(self) -> Optional[Dict]:
        """Get the next command from the queue"""
        try:
            priority, command_id, queue_item = self.command_queue.get_nowait()
            return queue_item
        except queue.Empty:
            return None

    def mark_command_started(self, command_id: str):
        """Mark a command as started"""
        with self.lock:
            self.active_threads += 1
            self.stats['last_activity'] = time.time()
            logger.info(f"🔄 Started command {command_id} (active: {self.active_threads}/{self.max_threads})")

    def mark_command_completed(self, command_id: str, success: bool, records_processed: int = 0,
                              error_message: str = None):
        """Mark a command as completed"""
        with self.lock:
            self.active_threads -= 1

            if success:
                self.completed_commands.append(command_id)
                self.stats['completed_commands'] += 1
                self.stats['total_records'] += records_processed
                logger.info(f"✅ Completed command {command_id} - {records_processed} records")
            else:
                self.failed_commands.append(command_id)
                self.stats['failed_commands'] += 1
                if error_message:
                    logger.error(f"❌ Failed command {command_id}: {error_message}")
                else:
                    logger.error(f"❌ Failed command {command_id}")

            self.stats['last_activity'] = time.time()
            logger.info(f"📊 Active threads: {self.active_threads}/{self.max_threads}")

    def can_start_new_command(self) -> bool:
        """Check if we can start a new command"""
        return self.active_threads < self.max_threads

    def get_stats(self) -> Dict:
        """Get current statistics"""
        with self.lock:
            elapsed_time = time.time() - self.stats['start_time']
            success_rate = 0
            if self.stats['total_commands'] > 0:
                success_rate = (self.stats['completed_commands'] / self.stats['total_commands']) * 100

            return {
                **self.stats,
                'elapsed_time': elapsed_time,
                'active_threads': self.active_threads,
                'max_threads': self.max_threads,
                'success_rate': success_rate,
                'commands_per_hour': (self.stats['completed_commands'] + self.stats['failed_commands']) / (elapsed_time / 3600) if elapsed_time > 0 else 0
            }

    def stop(self):
        """Stop the queue manager"""
        self.running = False
        logger.info("🛑 Command queue manager stopping...")

class CommandExecutor:
    """Executes commands and tracks their results"""

    def __init__(self, timeout: int = 3600):  # 1 hour default timeout
        self.timeout = timeout
        self.active_processes = {}
        self.lock = threading.Lock()

    def execute_command(self, command_id: str, command: str) -> Tuple[bool, int, str]:
        """Execute a command and return results"""
        logger.info(f"🚀 Executing {command_id}: {command}")

        try:
            # Start the process
            process = subprocess.Popen(
                command,
                shell=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                cwd=os.getcwd()
            )

            # Track the process
            with self.lock:
                self.active_processes[command_id] = {
                    'process': process,
                    'start_time': time.time(),
                    'command': command
                }

            # Wait for completion with timeout
            try:
                stdout, stderr = process.communicate(timeout=self.timeout)
                exit_code = process.returncode

                # Parse records processed from output
                records_processed = self._extract_records_count(stdout, stderr)

                success = exit_code == 0
                error_message = stderr if not success else None

                logger.info(f"📊 Command {command_id} completed: {records_processed} records, exit code {exit_code}")

                return success, records_processed, error_message or ""

            except subprocess.TimeoutExpired:
                process.kill()
                logger.error(f"⏰ Command {command_id} timed out after {self.timeout} seconds")
                return False, 0, f"Timeout after {self.timeout} seconds"

        except Exception as e:
            logger.error(f"💥 Command {command_id} failed with exception: {e}")
            return False, 0, str(e)

        finally:
            # Clean up process tracking
            with self.lock:
                if command_id in self.active_processes:
                    del self.active_processes[command_id]

    def _extract_records_count(self, stdout: str, stderr: str) -> int:
        """Extract records processed count from command output"""
        try:
            # Look for common patterns in the output
            combined_output = stdout + stderr

            # Pattern 1: "Records: 12345"
            import re
            patterns = [
                r'Records?\s*(?:Processed|Saved|Found):\s*(\d+)',
                r'(\d+)\s*records?\s*processed',
                r'Records:\s*(\d+)',
                r'Total Records:\s*(\d+)',
                r'Successfully ingested (\d+)'
            ]

            for pattern in patterns:
                match = re.search(pattern, combined_output, re.IGNORECASE)
                if match:
                    return int(match.group(1))

            # If no pattern matches, try to find any number that might be records
            numbers = re.findall(r'\b(\d{4,})\b', combined_output)
            if numbers:
                # Return the largest number that looks like a record count
                return max(int(n) for n in numbers if int(n) < 1000000)

            return 0

        except Exception:
            return 0

    def force_kill_all(self):
        """Force kill all active processes"""
        with self.lock:
            for command_id, info in self.active_processes.items():
                try:
                    info['process'].kill()
                    logger.info(f"🔪 Force killed process {command_id}")
                except Exception as e:
                    logger.error(f"Failed to kill process {command_id}: {e}")
            self.active_processes.clear()

class InfiniteBulkIngestion:
    """Main class for infinite loop bulk ingestion"""

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.queue_manager = CommandQueueManager(config.get('max_threads', 10))
        self.executor = CommandExecutor(config.get('timeout', 3600))
        self.running = True

        # Create necessary directories
        os.makedirs('logs', exist_ok=True)
        os.makedirs('data', exist_ok=True)
        os.makedirs('reports', exist_ok=True)

        logger.info(f"🚀 Infinite bulk ingestion initialized with {config.get('max_threads', 10)} threads")

    def generate_20_year_commands(self) -> List[Dict[str, Any]]:
        """Generate comprehensive commands for 20 years of data"""
        commands = []
        current_year = datetime.now().year
        start_year = current_year - 20  # Go back 20 years

        logger.info(f"📅 Generating commands for years {start_year}-{current_year}")

        # Congress commands (every Congress since start_year)
        for congress_num in range(107, 120):  # Congress 107 (2001-2003) to 119 (2025-2027)
            priority = 1 if congress_num >= 118 else 3  # Higher priority for recent

            commands.append({
                'command': f"python3 scripts/comprehensive_data_ingestion.py --source congress --congress {congress_num} --debug",
                'priority': priority,
                'description': f"Congress {congress_num} data ingestion"
            })

        # State-level OpenStates commands (top 20 states)
        top_states = [
            'ca', 'tx', 'fl', 'ny', 'pa', 'il', 'oh', 'ga', 'nc', 'mi',
            'wa', 'nj', 'va', 'az', 'ma', 'tn', 'in', 'mo', 'md', 'wi'
        ]

        for state in top_states:
            for year in range(start_year, current_year + 1):
                commands.append({
                    'command': f"python3 scripts/comprehensive_data_ingestion.py --source openstates --jurisdiction {state} --year {year} --debug",
                    'priority': 2,
                    'description': f"OpenStates {state} {year} data ingestion"
                })

        # GovInfo commands (major document types by year)
        collections = ['BILLS', 'CRPT', 'CREC', 'STAT', 'GAO']

        for collection in collections:
            for year in range(start_year, current_year + 1):
                commands.append({
                    'command': f"python3 scripts/comprehensive_data_ingestion.py --source govinfo --collection {collection} --year {year} --debug",
                    'priority': 3,
                    'description': f"GovInfo {collection} {year} data ingestion"
                })

        # Additional bulk commands for specific high-value data
        priority_commands = [
            {
                'command': "python3 scripts/comprehensive_bulk_ingestion.py --congresses 117 118 119 --debug",
                'priority': 1,
                'description': "Bulk Congress ingestion for recent sessions"
            },
            {
                'command': "python3 scripts/parallel_bulk_ingestion.py --debug --max-workers 20",
                'priority': 1,
                'description': "Parallel bulk ingestion with maximum workers"
            },
            {
                'command': "python3 scripts/comprehensive_data_ingestion.py --source all --debug",
                'priority': 1,
                'description': "Comprehensive all-source ingestion"
            }
        ]

        # Add priority commands
        commands.extend(priority_commands)

        # Shuffle commands within priority levels for better distribution
        commands.sort(key=lambda x: (x['priority'], x['command']))

        logger.info(f"📋 Generated {len(commands)} commands for 20-year data coverage")

        return commands

    def generate_custom_commands(self, command_file: str) -> List[Dict[str, Any]]:
        """Load commands from a file (one per line)"""
        commands = []

        try:
            with open(command_file, 'r') as f:
                for line_num, line in enumerate(f, 1):
                    line = line.strip()
                    if line and not line.startswith('#'):
                        commands.append({
                            'command': line,
                            'priority': 2,
                            'description': f"Custom command from {command_file}:{line_num}"
                        })

            logger.info(f"📋 Loaded {len(commands)} commands from {command_file}")

        except FileNotFoundError:
            logger.error(f"❌ Command file not found: {command_file}")

        return commands

    def load_commands(self) -> List[Dict[str, Any]]:
        """Load commands based on configuration"""
        commands = []

        # Check for custom command file
        if self.config.get('command_file'):
            commands.extend(self.generate_custom_commands(self.config['command_file']))
        else:
            # Generate 20-year commands
            commands.extend(self.generate_20_year_commands())

        # Add commands to queue
        for cmd_info in commands:
            self.queue_manager.add_command(
                command=cmd_info['command'],
                priority=cmd_info['priority']
            )

        return commands

    def process_command(self, command_info: Dict[str, Any]) -> bool:
        """Process a single command"""
        command_id = command_info['id']
        command = command_info['command']

        try:
            # Mark command as started
            self.queue_manager.mark_command_started(command_id)

            # Execute the command
            success, records_processed, error_message = self.executor.execute_command(command_id, command)

            # Mark command as completed
            self.queue_manager.mark_command_completed(command_id, success, records_processed, error_message)

            return success

        except Exception as e:
            logger.error(f"💥 Error processing command {command_id}: {e}")
            logger.debug(traceback.format_exc())

            self.queue_manager.mark_command_completed(command_id, False, 0, str(e))
            return False

    def run_infinite_loop(self):
        """Main infinite loop for processing commands"""
        logger.info("🔄 Starting infinite loop ingestion")

        # Load initial commands
        commands = self.load_commands()

        # Track statistics
        last_stats_time = time.time()
        stats_interval = 300  # Report stats every 5 minutes

        try:
            while self.running:
                # Check if we can start new commands
                while self.queue_manager.can_start_new_command():
                    # Get next command from queue
                    command_info = self.queue_manager.get_next_command()

                    if command_info is None:
                        # No more commands in queue
                        if self.queue_manager.active_threads == 0:
                            # All work is done
                            logger.info("🎉 All commands completed!")

                            # If not infinite mode, break
                            if not self.config.get('infinite', False):
                                break

                            # In infinite mode, generate new commands
                            time.sleep(60)  # Wait 1 minute before generating new work
                            commands = self.load_commands()
                            logger.info("🔄 Generated new batch of commands")
                        else:
                            # Commands are still running, wait
                            time.sleep(1)

                        break

                    # Process command in a separate thread
                    def process_wrapper(cmd_info):
                        self.process_command(cmd_info)

                    thread = threading.Thread(
                        target=process_wrapper,
                        args=(command_info,),
                        daemon=True
                    )
                    thread.start()

                # Periodically report statistics
                current_time = time.time()
                if current_time - last_stats_time >= stats_interval:
                    self._report_statistics()
                    last_stats_time = current_time

                # Check if we've been idle too long
                idle_time = current_time - self.queue_manager.stats['last_activity']
                if idle_time > 3600:  # 1 hour of inactivity
                    logger.warning("⚠️  System has been idle for over 1 hour, checking for new work...")
                    if self.queue_manager.active_threads == 0:
                        self.load_commands()
                        logger.info("📋 Loaded new batch of commands")

        except KeyboardInterrupt:
            logger.info("🛑 Received interrupt signal")

        finally:
            self._cleanup()

    def _report_statistics(self):
        """Report current statistics"""
        stats = self.queue_manager.get_stats()

        elapsed_hours = stats['elapsed_time'] / 3600
        avg_commands_per_hour = stats['commands_per_hour']

        logger.info("📊 STATISTICS REPORT")
        logger.info(f"  ⏰ Runtime: {elapsed_hours:.1f} hours")
        logger.info(f"  📋 Total Commands: {stats['total_commands']}")
        logger.info(f"  ✅ Completed: {stats['completed_commands']}")
        logger.info(f"  ❌ Failed: {stats['failed_commands']}")
        logger.info(f"  📈 Success Rate: {stats['success_rate']:.1f}%")
        logger.info(f"  📄 Records Processed: {stats['total_records']:,}")
        logger.info(f"  🚀 Commands/Hour: {avg_commands_per_hour:.1f}")
        logger.info(f"  🔄 Active Threads: {stats['active_threads']}/{stats['max_threads']}")

        # Save periodic report
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        report_file = f"reports/ingestion_stats_{timestamp}.json"

        with open(report_file, 'w') as f:
            json.dump(stats, f, indent=2, default=str)

        logger.info(f"  📄 Report saved: {report_file}")

    def _cleanup(self):
        """Cleanup resources"""
        logger.info("🧹 Cleaning up resources...")

        # Stop accepting new commands
        self.running = False

        # Force kill all running processes
        self.executor.force_kill_all()

        # Stop queue manager
        self.queue_manager.stop()

        # Generate final report
        final_stats = self.queue_manager.get_stats()
        final_report = {
            'timestamp': datetime.now().isoformat(),
            'status': 'completed',
            'statistics': final_stats,
            'configuration': self.config
        }

        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        report_file = f"reports/final_ingestion_report_{timestamp}.json"

        with open(report_file, 'w') as f:
            json.dump(final_report, f, indent=2, default=str)

        logger.info(f"📄 Final report saved: {report_file}")

        # Print final summary
        elapsed_time = final_stats['elapsed_time'] / 3600
        print("\n" + "="*80)
        print("🎉 INFINITE BULK INGESTION COMPLETED")
        print("="*80)
        print(f"⏰ Total Runtime: {elapsed_time:.1f} hours")
        print(f"📋 Total Commands: {final_stats['total_commands']}")
        print(f"✅ Completed: {final_stats['completed_commands']}")
        print(f"❌ Failed: {final_stats['failed_commands']}")
        print(f"📈 Success Rate: {final_stats['success_rate']:.1f}%")
        print(f"📄 Records Processed: {final_stats['total_records']:,}")
        print(f"📄 Final Report: {report_file}")
        print("="*80)

def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description='Infinite Loop Bulk Data Ingestion')
    parser.add_argument('--command-file', type=str,
                       help='File containing commands (one per line)')
    parser.add_argument('--max-threads', type=int, default=10,
                       help='Maximum number of concurrent threads')
    parser.add_argument('--timeout', type=int, default=3600,
                       help='Command timeout in seconds (default: 3600)')
    parser.add_argument('--infinite', action='store_true',
                       help='Run in infinite mode, generating new commands continuously')
    parser.add_argument('--debug', action='store_true',
                       help='Enable debug logging')
    parser.add_argument('--dry-run', action='store_true',
                       help='Show what commands would be executed without running them')

    args = parser.parse_args()

    # Configure logging
    if args.debug:
        logging.getLogger().setLevel(logging.DEBUG)

    # Load configuration
    config = {
        'command_file': args.command_file,
        'max_threads': args.max_threads,
        'timeout': args.timeout,
        'infinite': args.infinite,
        'debug': args.debug,
        'dry_run': args.dry_run
    }

    logger.info("🚀 Initializing infinite bulk ingestion system")
    logger.info(f"  Max Threads: {args.max_threads}")
    logger.info(f"  Timeout: {args.timeout}s")
    logger.info(f"  Infinite Mode: {args.infinite}")

    if args.dry_run:
        logger.info("🧪 DRY RUN MODE - Showing commands without executing")

        # Initialize ingestion system
        ingestion = InfiniteBulkIngestion(config)

        # Generate commands and display them
        commands = ingestion.generate_20_year_commands()

        print(f"\n🧪 DRY RUN: Generated {len(commands)} commands")
        print("="*80)

        for i, cmd in enumerate(commands[:50]):  # Show first 50
            print(f"{i+1:3d}. [{cmd['priority']}] {cmd['command']}")

        if len(commands) > 50:
            print(f"... and {len(commands) - 50} more commands")

        print("="*80)
        logger.info("🧪 Dry run completed")
        return

    # Validate required environment variables
    required_env_vars = [
        'CONGRESS_API_KEY',
        'OPENSTATES_API_KEY',
        'GOVINFO_API_KEY'
    ]

    missing_vars = []
    for var in required_env_vars:
        if not os.getenv(var):
            missing_vars.append(var)

    if missing_vars:
        logger.error(f"❌ Missing required environment variables: {missing_vars}")
        logger.error("Please set these variables before running:")
        for var in missing_vars:
            logger.error(f"  export {var}=your_api_key_here")
        sys.exit(1)

    logger.info("✅ All required environment variables found")

    # Handle signals for graceful shutdown
    def signal_handler(signum, frame):
        logger.info(f"🛑 Received signal {signum}")
        sys.exit(0)

    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    # Initialize and run ingestion system
    ingestion = InfiniteBulkIngestion(config)
    ingestion.run_infinite_loop()

if __name__ == "__main__":
    main()
