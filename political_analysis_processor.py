#!/usr/bin/env python3
"""
OpenDiscourse Political Analysis Processor

This script analyzes bills for political bias, freedom impact,
and content safety including hate speech detection.
"""

import os
import sys
import logging
import argparse
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from datetime import datetime
import time

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import psycopg2
from psycopg2.extras import DictCursor
from dotenv import load_dotenv

# Load environment
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


@dataclass
class PoliticalAnalysisConfig:
    """Configuration for political analysis"""

    model_name: str = "political_bias_v1"
    batch_size: int = 100
    bias_tolerance: float = 0.2
    freedom_tolerance: float = 0.2
    hate_speech_threshold: float = 0.1
    inflammatory_threshold: float = 0.2


class PoliticalAnalysisProcessor:
    """Process bills for political analysis"""

    def __init__(self, config: PoliticalAnalysisConfig):
        self.config = config
        self.setup_database_connection()

    def setup_database_connection(self):
        """Setup database connection"""
        try:
            db_host = os.getenv("DB_HOST", "/var/run/postgresql")
            db_port = os.getenv("DB_PORT", "5432")
            db_name = os.getenv("DB_NAME", "opendiscourse")
            db_user = os.getenv("DB_USER", "cbwinslow")

            self.conn = psycopg2.connect(
                dbname=db_name,
                user=db_user,
                host=db_host,
                port=db_port,
            )
            self.cursor = self.conn.cursor(cursor_factory=DictCursor)
            logger.info("Database connection established")

        except Exception as e:
            logger.error(f"Database connection failed: {e}")
            raise

    def get_unanalyzed_bills(self, batch_size: int = None) -> List[Dict[str, Any]]:
        """Get bills pending political analysis"""
        if batch_size is None:
            batch_size = self.config.batch_size

        query = """
        SELECT 
            b.bill_id,
            b.official_title,
            b.summary_text,
            b.congress_number,
            b.bill_type,
            b.sponsor_bioguide_id,
            b.introduced_date,
            m.first_name || ' ' || m.last_name as sponsor_name,
            mt.party_code as sponsor_party
        FROM congress.bills b
        LEFT JOIN congress.members m ON b.sponsor_bioguide_id = m.bioguide_id
        LEFT JOIN congress.member_terms mt ON b.sponsor_bioguide_id = mt.bioguide_id 
            AND mt.start_date <= b.introduced_date 
            AND (mt.end_date >= b.introduced_date OR mt.end_date IS NULL)
        WHERE b.bill_id NOT IN (
            SELECT bill_id FROM analysis.bill_political_scores 
            WHERE model_name = %s
        )
        LIMIT %s
        """

        self.cursor.execute(query, (self.config.model_name, batch_size))
        return [dict(row) for row in self.cursor.fetchall()]

    def analyze_bill_batch(self, bills: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze a batch of bills for political content"""
        if not bills:
            return {"processed": 0, "success": True, "message": "No bills to analyze"}

        logger.info(f"Analyzing {len(bills)} bills for political content")

        processed_count = 0
        error_count = 0

        for bill in bills:
            try:
                # Call the PostgreSQL function to classify the bill
                self.cursor.execute(
                    "SELECT analysis.classify_bill_politically(%s, %s)",
                    (bill["bill_id"], self.config.model_name),
                )
                self.conn.commit()
                processed_count += 1

            except Exception as e:
                logger.error(f"Error analyzing bill {bill['bill_id']}: {e}")
                error_count += 1
                self.conn.rollback()

        result = {
            "processed": processed_count,
            "errors": error_count,
            "total": len(bills),
            "success": processed_count > 0,
            "message": f"Processed {processed_count} bills, {error_count} errors",
        }

        logger.info(result["message"])
        return result

    def get_political_statistics(
        self, congress_number: int = None, party_filter: str = None
    ) -> Dict[str, Any]:
        """Get political analysis statistics"""
        query = """
        SELECT * FROM analysis.get_political_statistics(%s, %s)
        """

        self.cursor.execute(query, (congress_number, party_filter))
        result = dict(self.cursor.fetchone())

        return result

    def get_problematic_bills(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Get bills with problematic content"""
        query = """
        SELECT * FROM analysis.problematic_bills
        ORDER BY 
            hate_speech_score DESC,
            inflammatory_language_score DESC,
            divisive_language_score DESC
        LIMIT %s
        """

        self.cursor.execute(query, (limit,))
        return [dict(row) for row in self.cursor.fetchall()]

    def find_politically_similar_bills(
        self, bill_id: str, limit: int = 10
    ) -> List[Dict[str, Any]]:
        """Find bills with similar political characteristics"""
        query = """
        SELECT * FROM analysis.find_politically_similar_bills(
            %s, %s, %s, %s
        )
        """

        self.cursor.execute(
            query,
            (bill_id, self.config.bias_tolerance, self.config.freedom_tolerance, limit),
        )
        return [dict(row) for row in self.cursor.fetchall()]

    def get_bill_political_analysis(self, bill_id: str) -> Dict[str, Any]:
        """Get complete political analysis for a specific bill"""
        query = """
        SELECT * FROM analysis.get_bill_political_analysis(%s)
        """

        self.cursor.execute(query, (bill_id,))
        result = self.cursor.fetchone()

        return dict(result) if result else None

    def run_full_analysis(self) -> Dict[str, Any]:
        """Run political analysis on all bills"""
        logger.info("Starting full political analysis")

        batch_count = 0
        total_processed = 0
        total_errors = 0

        while True:
            batch_count += 1
            logger.info(f"Processing batch {batch_count}")

            bills = self.get_unanalyzed_bills()
            if not bills:
                logger.info("All bills analyzed")
                break

            result = self.analyze_bill_batch(bills)

            total_processed += result["processed"]
            total_errors += result["errors"]

            # Small delay to avoid overwhelming database
            time.sleep(0.1)

        # Final statistics
        final_stats = self.get_political_statistics()

        logger.info("=" * 50)
        logger.info("POLITICAL ANALYSIS COMPLETE")
        logger.info(f"Total batches: {batch_count}")
        logger.info(f"Total processed: {total_processed}")
        logger.info(f"Total errors: {total_errors}")
        logger.info(f"Average bias score: {final_stats.get('avg_bias_score', 0):.3f}")
        logger.info(
            f"Average freedom score: {final_stats.get('avg_freedom_score', 0):.3f}"
        )
        logger.info("=" * 50)

        return {
            "total_batches": batch_count,
            "total_processed": total_processed,
            "total_errors": total_errors,
            "statistics": final_stats,
        }

    def generate_political_report(self) -> Dict[str, Any]:
        """Generate comprehensive political analysis report"""
        logger.info("Generating political analysis report")

        # Get overall statistics
        overall_stats = self.get_political_statistics()

        # Get problematic bills
        problematic_bills = self.get_problematic_bills(20)

        # Get political distribution
        query = """
        SELECT 
            overall_political_lean,
            COUNT(*) as count,
            AVG(political_bias_score) as avg_bias,
            AVG(freedom_score) as avg_freedom,
            AVG(hate_speech_score) as avg_hate_speech
        FROM analysis.political_analysis_summary
        GROUP BY overall_political_lean
        ORDER BY count DESC
        """

        self.cursor.execute(query)
        political_distribution = [dict(row) for row in self.cursor.fetchall()]

        # Get party-specific statistics
        query = """
        SELECT 
            sponsor_party,
            COUNT(*) as bill_count,
            AVG(political_bias_score) as avg_bias,
            AVG(freedom_score) as avg_freedom,
            AVG(hate_speech_score) as avg_hate_speech,
            COUNT(CASE WHEN content_safety_rating IN ('Problematic', 'Harmful') THEN 1 END) as problematic_count
        FROM analysis.political_analysis_summary
        WHERE sponsor_party IS NOT NULL
        GROUP BY sponsor_party
        ORDER BY bill_count DESC
        """

        self.cursor.execute(query)
        party_stats = [dict(row) for row in self.cursor.fetchall()]

        report = {
            "generated_at": datetime.now().isoformat(),
            "model_name": self.config.model_name,
            "overall_statistics": overall_stats,
            "political_distribution": political_distribution,
            "party_statistics": party_stats,
            "problematic_bills": problematic_bills,
            "analysis_parameters": {
                "bias_tolerance": self.config.bias_tolerance,
                "freedom_tolerance": self.config.freedom_tolerance,
                "hate_speech_threshold": self.config.hate_speech_threshold,
                "inflammatory_threshold": self.config.inflammatory_threshold,
            },
        }

        return report

    def save_report_to_file(self, report: Dict[str, Any], filename: str = None):
        """Save political analysis report to file"""
        if filename is None:
            filename = f"political_analysis_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"

        import json

        with open(filename, "w") as f:
            json.dump(report, f, indent=2, default=str)

        logger.info(f"Political analysis report saved to {filename}")


def main():
    """Main function"""
    parser = argparse.ArgumentParser(description="Analyze political content of bills")
    parser.add_argument(
        "--model", type=str, default="political_bias_v1", help="Model name for analysis"
    )
    parser.add_argument(
        "--batch-size", type=int, default=100, help="Batch size for processing"
    )
    parser.add_argument(
        "--bias-tolerance",
        type=float,
        default=0.2,
        help="Tolerance for political bias similarity",
    )
    parser.add_argument(
        "--freedom-tolerance",
        type=float,
        default=0.2,
        help="Tolerance for freedom score similarity",
    )
    parser.add_argument(
        "--full-analysis", action="store_true", help="Run full analysis on all bills"
    )
    parser.add_argument("--bill-id", type=str, help="Analyze specific bill")
    parser.add_argument("--congress", type=int, help="Filter by congress number")
    parser.add_argument("--party", type=str, help="Filter by sponsor party")
    parser.add_argument(
        "--problematic", action="store_true", help="Show problematic bills"
    )
    parser.add_argument(
        "--report", action="store_true", help="Generate comprehensive report"
    )
    parser.add_argument(
        "--stats", action="store_true", help="Show political statistics"
    )
    parser.add_argument("--setup", action="store_true", help="Setup database schema")

    args = parser.parse_args()

    # Create configuration
    config = PoliticalAnalysisConfig(
        model_name=args.model,
        batch_size=args.batch_size,
        bias_tolerance=args.bias_tolerance,
        freedom_tolerance=args.freedom_tolerance,
    )

    # Setup database schema if requested
    if args.setup:
        logger.info("Setting up political analysis schema...")
        try:
            with open("political_analysis_functions.sql", "r") as f:
                schema_sql = f.read()

            conn = psycopg2.connect(
                dbname=os.getenv("DB_NAME", "opendiscourse"),
                user=os.getenv("DB_USER", "cbwinslow"),
                host=os.getenv("DB_HOST", "/var/run/postgresql"),
                port=os.getenv("DB_PORT", "5432"),
            )
            cursor = conn.cursor()
            cursor.execute(schema_sql)
            conn.commit()
            conn.close()

            logger.info("Political analysis schema setup completed")

        except Exception as e:
            logger.error(f"Schema setup failed: {e}")
            sys.exit(1)

        return

    # Create processor
    try:
        processor = PoliticalAnalysisProcessor(config)

        # Show statistics if requested
        if args.stats:
            stats = processor.get_political_statistics(args.congress, args.party)
            print("\n" + "=" * 50)
            print("POLITICAL ANALYSIS STATISTICS")
            print("=" * 50)
            print(f"Total bills: {stats.get('total_bills', 0)}")
            print(f"Average bias score: {stats.get('avg_bias_score', 0):.3f}")
            print(f"Average freedom score: {stats.get('avg_freedom_score', 0):.3f}")
            print(f"Far Left: {stats.get('far_left_count', 0)}")
            print(f"Left: {stats.get('left_count', 0)}")
            print(f"Center-Left: {stats.get('center_left_count', 0)}")
            print(f"Center: {stats.get('center_count', 0)}")
            print(f"Center-Right: {stats.get('center_right_count', 0)}")
            print(f"Right: {stats.get('right_count', 0)}")
            print(f"Far Right: {stats.get('far_right_count', 0)}")
            print(f"Problematic content: {stats.get('problematic_content_count', 0)}")
            print(f"Hate speech indicators: {stats.get('hate_speech_count', 0)}")
            print("=" * 50)
            return

        # Show problematic bills if requested
        if args.problematic:
            problematic = processor.get_problematic_bills()
            print(f"\nFound {len(problematic)} problematic bills:")
            for i, bill in enumerate(problematic[:10], 1):
                print(f"{i}. {bill['bill_title']}")
                print(f"   Bias: {bill.get('political_bias_score', 0):.3f}")
                print(f"   Hate Speech: {bill.get('hate_speech_score', 0):.3f}")
                print(
                    f"   Safety Rating: {bill.get('content_safety_rating', 'Unknown')}"
                )
                print()
            return

        # Analyze specific bill if requested
        if args.bill_id:
            analysis = processor.get_bill_political_analysis(args.bill_id)
            if analysis:
                print(f"\nPolitical Analysis for Bill: {analysis['bill_title']}")
                print(
                    f"Sponsor: {analysis['sponsor_name']} ({analysis['sponsor_party']})"
                )
                print(f"Political Lean: {analysis['overall_political_lean']}")
                print(f"Bias Score: {analysis['political_bias_score']:.3f}")
                print(f"Freedom Score: {analysis['freedom_score']:.3f}")
                print(f"Content Safety: {analysis['content_safety_rating']}")
                print(f"Hate Speech Score: {analysis['hate_speech_score']:.3f}")

                # Find similar bills
                similar = processor.find_politically_similar_bills(args.bill_id, 5)
                if similar:
                    print(f"\nPolitically Similar Bills:")
                    for bill in similar:
                        print(
                            f"  - {bill['bill_title']} ({bill['overall_political_lean']})"
                        )
            else:
                print("Bill not found or not analyzed")
            return

        # Generate comprehensive report if requested
        if args.report:
            report = processor.generate_political_report()
            processor.save_report_to_file(report)

            print("\n" + "=" * 50)
            print("POLITICAL ANALYSIS REPORT")
            print("=" * 50)
            print(
                f"Total bills analyzed: {report['overall_statistics'].get('total_bills', 0)}"
            )
            print(
                f"Average bias score: {report['overall_statistics'].get('avg_bias_score', 0):.3f}"
            )
            print(
                f"Average freedom score: {report['overall_statistics'].get('avg_freedom_score', 0):.3f}"
            )
            print(
                f"Problematic bills: {report['overall_statistics'].get('problematic_content_count', 0)}"
            )
            print(
                f"Hate speech indicators: {report['overall_statistics'].get('hate_speech_count', 0)}"
            )
            print("\nPolitical Distribution:")
            for dist in report["political_distribution"]:
                print(f"  {dist['overall_political_lean']}: {dist['count']} bills")
            print("\nReport saved to file")
            print("=" * 50)
            return

        # Run full analysis if requested
        if args.full_analysis:
            result = processor.run_full_analysis()

            print("\n" + "=" * 50)
            print("FULL POLITICAL ANALYSIS COMPLETE")
            print("=" * 50)
            print(f"Total batches: {result['total_batches']}")
            print(f"Total processed: {result['total_processed']}")
            print(f"Total errors: {result['total_errors']}")
            print(
                f"Average bias score: {result['statistics'].get('avg_bias_score', 0):.3f}"
            )
            print(
                f"Average freedom score: {result['statistics'].get('avg_freedom_score', 0):.3f}"
            )
            print("=" * 50)
            return

        # Show usage if no specific action
        print("Use --help to see available options")
        print("Examples:")
        print("  --stats                    Show political statistics")
        print("  --problematic              Show problematic bills")
        print("  --bill-id <id>           Analyze specific bill")
        print("  --report                   Generate comprehensive report")
        print("  --full-analysis             Analyze all bills")

    except KeyboardInterrupt:
        logger.info("Analysis interrupted by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Analysis failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
