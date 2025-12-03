#!/usr/bin/env python3
"""
Phase 6: Final Verification and Reporting

This script handles the final verification phase:
- Verifies completion of all ingestion phases
- Generates comprehensive reports
- Validates data integrity and completeness
- Provides final status and recommendations

ASSIGNED TO: AI Agent responsible for final verification
DEPENDENCIES: All previous phases must complete successfully
"""

import os
import sys
import json
import psycopg2
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Tuple

# Add project path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from ingestion_config import validate_all_api_keys, get_ingestion_mode_from_env

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

class Phase6Verification:
    """Phase 6: Final Verification and Reporting"""

    def __init__(self):
        self.phase_start = datetime.now()
        self.verification_results = {}

        # Validate prerequisites
        self._validate_prerequisites()

    def _validate_prerequisites(self):
        """Validate prerequisites"""
        print("🔍 Validating prerequisites...")

        # Check API keys
        key_validation = validate_all_api_keys()
        if not key_validation['valid']:
            raise ValueError("API keys validation failed")

        print("✅ Prerequisites validated")

    def _execute_query(self, query: str) -> List[Dict[str, Any]]:
        """Execute a query safely"""
        try:
            fresh_conn = psycopg2.connect(database='cbwinslow', user='cbwinslow')
            fresh_cursor = fresh_conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
            fresh_conn.autocommit = True

            fresh_cursor.execute(query)
            columns = [desc[0] for desc in fresh_cursor.description]
            results = []

            for row in fresh_cursor.fetchall():
                result_dict = dict(zip(columns, row))
                # Convert datetime objects to strings
                for key, value in result_dict.items():
                    if isinstance(value, datetime):
                        result_dict[key] = value.isoformat()
                results.append(result_dict)

            fresh_cursor.close()
            fresh_conn.close()
            return results

        except Exception as e:
            print(f"Error executing query: {e}")
            return []

    def verify_checkpoint_completion(self) -> Dict[str, Any]:
        """Verify all checkpoints are completed"""
        print("📋 Verifying checkpoint completion...")

        query = """
            SELECT
                data_source,
                data_type,
                category,
                total_processed,
                total_estimated,
                completion_percentage,
                is_completed,
                last_ingestion_at,
                status
            FROM incremental.checkpoint_status
            ORDER BY data_source, data_type, category
        """

        checkpoints = self._execute_query(query)

        total_checkpoints = len(checkpoints)
        completed_checkpoints = sum(1 for cp in checkpoints if cp['is_completed'])
        completion_rate = (completed_checkpoints / total_checkpoints * 100) if total_checkpoints > 0 else 0

        verification = {
            'total_checkpoints': total_checkpoints,
            'completed_checkpoints': completed_checkpoints,
            'completion_rate': completion_rate,
            'checkpoint_details': checkpoints,
            'status': 'PASS' if completion_rate >= 95 else 'FAIL',
            'issues': [cp for cp in checkpoints if not cp['is_completed']]
        }

        print(f"📊 Checkpoints: {completed_checkpoints}/{total_checkpoints} ({completion_rate:.1f}%)")
        return verification

    def verify_data_integrity(self) -> Dict[str, Any]:
        """Verify data integrity and quality"""
        print("🔍 Verifying data integrity...")

        integrity_checks = {}

        # Check Congress members
        members_query = """
            SELECT
                COUNT(*) as total_members,
                COUNT(DISTINCT bioguide_id) as unique_members,
                COUNT(CASE WHEN bioguide_id IS NOT NULL THEN 1 END) as has_bioguide_id,
                COUNT(CASE WHEN official_full_name IS NOT NULL THEN 1 END) as has_full_name,
                MIN(created_at) as first_ingested,
                MAX(created_at) as last_ingested
            FROM congress.members
        """

        integrity_checks['members'] = {
            'query_result': self._execute_query(members_query)[0],
            'duplicate_rate': 0,  # Will be calculated
            'completeness_rate': 0  # Will be calculated
        }

        # Check Congress bills
        bills_query = """
            SELECT
                COUNT(*) as total_bills,
                COUNT(DISTINCT bill_id) as unique_bills,
                COUNT(CASE WHEN bill_id IS NOT NULL THEN 1 END) as has_bill_id,
                COUNT(CASE WHEN official_title IS NOT NULL THEN 1 END) as has_title,
                MIN(created_at) as first_ingested,
                MAX(created_at) as last_ingested
            FROM congress.bills
        """

        integrity_checks['bills'] = {
            'query_result': self._execute_query(bills_query)[0],
            'duplicate_rate': 0,
            'completeness_rate': 0
        }

        # Calculate duplicate and completeness rates
        members_data = integrity_checks['members']['query_result']
        if members_data['total_members'] > 0:
            integrity_checks['members']['duplicate_rate'] = (
                (members_data['total_members'] - members_data['unique_members']) / members_data['total_members'] * 100
            )
            integrity_checks['members']['completeness_rate'] = (
                members_data['has_bioguide_id'] / members_data['total_members'] * 100
            )

        bills_data = integrity_checks['bills']['query_result']
        if bills_data['total_bills'] > 0:
            integrity_checks['bills']['duplicate_rate'] = (
                (bills_data['total_bills'] - bills_data['unique_bills']) / bills_data['total_bills'] * 100
            )
            integrity_checks['bills']['completeness_rate'] = (
                bills_data['has_bill_id'] / bills_data['total_bills'] * 100
            )

        # Overall integrity status
        overall_status = 'PASS'
        issues = []

        for data_type, check in integrity_checks.items():
            if check['duplicate_rate'] > 5:  # More than 5% duplicates
                overall_status = 'FAIL'
                issues.append(f"High duplicate rate in {data_type}: {check['duplicate_rate']:.1f}%")

            if check['completeness_rate'] < 90:  # Less than 90% complete
                overall_status = 'FAIL'
                issues.append(f"Low completeness in {data_type}: {check['completeness_rate']:.1f}%")

        verification = {
            'integrity_checks': integrity_checks,
            'overall_status': overall_status,
            'issues': issues
        }

        print(f"🔍 Data Integrity: {overall_status}")
        return verification

    def verify_expected_volumes(self) -> Dict[str, Any]:
        """Verify expected data volumes"""
        print("📊 Verifying expected data volumes...")

        volume_checks = {}

        # Expected volumes (approximate)
        expected_volumes = {
            'congress_members_116': 440,
            'congress_members_117': 550,
            'congress_members_118': 550,
            'congress_bills_117': 8000,
            'congress_bills_118': 8000,
            'openstates_people': 7500,
            'openstates_bills': 15000
        }

        # Get actual volumes
        actual_volumes = {}

        # Congress members by congress
        members_by_congress = """
            SELECT
                mt.congress_number,
                COUNT(DISTINCT m.bioguide_id) as count
            FROM congress.members m
            JOIN congress.member_terms mt ON m.bioguide_id = mt.bioguide_id
            WHERE mt.congress_number IN (116, 117, 118)
            GROUP BY mt.congress_number
            ORDER BY mt.congress_number
        """

        for row in self._execute_query(members_by_congress):
            actual_volumes[f'congress_members_{row["congress_number"]}'] = row['count']

        # Congress bills by congress
        bills_by_congress = """
            SELECT
                congress_number,
                COUNT(*) as count
            FROM congress.bills
            WHERE congress_number IN (117, 118)
            GROUP BY congress_number
            ORDER BY congress_number
        """

        for row in self._execute_query(bills_by_congress):
            actual_volumes[f'congress_bills_{row["congress_number"]}'] = row['count']

        # OpenStates data
        openstates_people = self._execute_query("SELECT COUNT(*) as count FROM openstates.people")[0]
        openstates_bills = self._execute_query("SELECT COUNT(*) as count FROM openstates.bills")[0]

        actual_volumes['openstates_people'] = openstates_people['count']
        actual_volumes['openstates_bills'] = openstates_bills['count']

        # Compare expected vs actual
        volume_comparisons = []
        total_expected = 0
        total_actual = 0

        for key, expected in expected_volumes.items():
            actual = actual_volumes.get(key, 0)
            completion_rate = (actual / expected * 100) if expected > 0 else 0

            total_expected += expected
            total_actual += actual

            volume_comparisons.append({
                'category': key,
                'expected': expected,
                'actual': actual,
                'completion_rate': completion_rate,
                'status': 'PASS' if completion_rate >= 80 else 'FAIL'
            })

        overall_completion = (total_actual / total_expected * 100) if total_expected > 0 else 0
        overall_status = 'PASS' if overall_completion >= 80 else 'FAIL'

        verification = {
            'expected_volumes': expected_volumes,
            'actual_volumes': actual_volumes,
            'volume_comparisons': volume_comparisons,
            'total_expected': total_expected,
            'total_actual': total_actual,
            'overall_completion_rate': overall_completion,
            'overall_status': overall_status
        }

        print(f"📊 Volume Verification: {overall_completion:.1f}% ({overall_status})")
        return verification

    def verify_api_compliance(self) -> Dict[str, Any]:
        """Verify API key compliance"""
        print("🔑 Verifying API compliance...")

        api_validation = validate_all_api_keys()
        mode = get_ingestion_mode_from_env()

        compliance_status = 'PASS'
        issues = []

        if not api_validation['valid']:
            compliance_status = 'FAIL'
            issues.extend(api_validation['errors'])

        if mode.value != 'production':
            compliance_status = 'FAIL'
            issues.append(f"Ingestion mode is {mode.value}, should be production")

        verification = {
            'api_validation': api_validation,
            'ingestion_mode': mode.value,
            'compliance_status': compliance_status,
            'issues': issues
        }

        print(f"🔑 API Compliance: {compliance_status}")
        return verification

    def generate_final_report(self) -> Dict[str, Any]:
        """Generate comprehensive final report"""
        print("\n" + "="*60)
        print("🏁 PHASE 6: FINAL VERIFICATION AND REPORTING")
        print("="*60)

        # Run all verifications
        checkpoint_verification = self.verify_checkpoint_completion()
        integrity_verification = self.verify_data_integrity()
        volume_verification = self.verify_expected_volumes()
        compliance_verification = self.verify_api_compliance()

        # Calculate overall status
        all_verifications = [
            checkpoint_verification['status'],
            integrity_verification['overall_status'],
            volume_verification['overall_status'],
            compliance_verification['compliance_status']
        ]

        overall_status = 'PASS' if all(v == 'PASS' for v in all_verifications) else 'FAIL'

        # Collect all issues
        all_issues = []
        all_issues.extend([f"Checkpoint: {issue}" for issue in checkpoint_verification['issues']])
        all_issues.extend(integrity_verification['issues'])
        all_issues.extend([f"Volume: {comp['category']} - {comp['completion_rate']:.1f}%"
                          for comp in volume_verification['volume_comparisons'] if comp['status'] == 'FAIL'])
        all_issues.extend(compliance_verification['issues'])

        # Generate summary statistics
        summary_stats = {
            'total_checkpoints': checkpoint_verification['total_checkpoints'],
            'completed_checkpoints': checkpoint_verification['completed_checkpoints'],
            'checkpoint_completion_rate': checkpoint_verification['completion_rate'],
            'total_records_ingested': volume_verification['total_actual'],
            'expected_total_records': volume_verification['total_expected'],
            'volume_completion_rate': volume_verification['overall_completion_rate'],
            'data_integrity_status': integrity_verification['overall_status'],
            'api_compliance_status': compliance_verification['compliance_status']
        }

        # Recommendations
        recommendations = []

        if overall_status == 'FAIL':
            recommendations.append("Address critical issues before proceeding to production")

        if checkpoint_verification['completion_rate'] < 100:
            recommendations.append("Complete all ingestion checkpoints")

        if volume_verification['overall_completion_rate'] < 90:
            recommendations.append("Review and complete missing data ingestion")

        if integrity_verification['overall_status'] == 'FAIL':
            recommendations.append("Fix data integrity issues (duplicates, missing fields)")

        if compliance_verification['compliance_status'] == 'FAIL':
            recommendations.append("Fix API key compliance issues")

        if overall_status == 'PASS':
            recommendations.append("Ingestion process completed successfully")
            recommendations.append("Ready for production deployment")

        final_report = {
            'phase': 6,
            'phase_name': 'Final Verification and Reporting',
            'start_time': self.phase_start.isoformat(),
            'end_time': datetime.now().isoformat(),
            'duration_seconds': (datetime.now() - self.phase_start).total_seconds(),
            'overall_status': overall_status,
            'summary_statistics': summary_stats,
            'verifications': {
                'checkpoint_completion': checkpoint_verification,
                'data_integrity': integrity_verification,
                'expected_volumes': volume_verification,
                'api_compliance': compliance_verification
            },
            'all_issues': all_issues,
            'recommendations': recommendations,
            'next_steps': 'PRODUCTION_READY' if overall_status == 'PASS' else 'ISSUES_TO_RESOLVE'
        }

        # Print summary
        print("\n" + "="*60)
        print(f"🏁 FINAL VERIFICATION SUMMARY: {overall_status}")
        print(f"📊 Checkpoints: {checkpoint_verification['completion_rate']:.1f}% complete")
        print(f"📈 Volumes: {volume_verification['overall_completion_rate']:.1f}% complete")
        print(f"🔍 Integrity: {integrity_verification['overall_status']}")
        print(f"🔑 Compliance: {compliance_verification['compliance_status']}")
        print(f"📄 Total Records: {volume_verification['total_actual']:,}")
        print(f"⏱️  Duration: {final_report['duration_seconds']:.1f} seconds")
        print("="*60)

        if all_issues:
            print(f"\n⚠️  ISSUES FOUND ({len(all_issues)}):")
            for issue in all_issues:
                print(f"   - {issue}")

        if recommendations:
            print(f"\n💡 RECOMMENDATIONS:")
            for rec in recommendations:
                print(f"   - {rec}")

        return final_report

    def save_verification_report(self, filename: str = None) -> str:
        """Save verification report to file"""
        if not filename:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"phase_6_final_verification_{timestamp}.json"

        report = self.generate_final_report()

        try:
            with open(filename, 'w') as f:
                json.dump(report, f, indent=2, default=str)

            print(f"📄 Verification report saved to: {filename}")
            return filename

        except Exception as e:
            print(f"❌ Error saving verification report: {e}")
            return ""

def main():
    """Main function"""
    import argparse

    parser = argparse.ArgumentParser(description='Phase 6: Final Verification and Reporting')
    parser.add_argument('--output', '-o', help='Output filename (default: auto-generated)')
    parser.add_argument('--save', action='store_true', help='Save results to file')

    args = parser.parse_args()

    try:
        verifier = Phase6Verification()

        if args.save:
            verifier.save_verification_report(args.output)
        else:
            verifier.generate_final_report()

        # Exit with appropriate code
        report = verifier.generate_final_report()
        sys.exit(0 if report['overall_status'] == 'PASS' else 1)

    except Exception as e:
        print(f"❌ Phase 6 verification failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
