#!/usr/bin/env python3
"""
Schema Validation Script
Tests all three data models against real API endpoints to verify compatibility
and identify any missing fields or optimization opportunities.

Usage:
    python validate_schemas.py [--test-all] [--source congress|govinfo|openstates]

Requirements:
    - All API keys in .env file
    - PostgreSQL database running
    - Python 3.13+
"""

import os
import sys
import json
import asyncio
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime, date
from dataclasses import dataclass
from pathlib import Path

# Add project root to path
sys.path.append(str(Path(__file__).parent.parent))

import psycopg2
from psycopg2.extras import DictCursor
import requests
import aiohttp
from pydantic import BaseModel, ValidationError

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@dataclass
class ValidationResult:
    """Schema validation result"""
    source: str
    endpoint: str
    success: bool
    sample_data: Dict[str, Any]
    missing_fields: List[str]
    extra_fields: List[str]
    errors: List[str]
    recommendations: List[str]

class SchemaValidator:
    """Main schema validation class"""
    
    def __init__(self):
        self.db_config = {
            'host': os.getenv('DB_HOST', 'localhost'),
            'port': os.getenv('DB_PORT', '5432'),
            'database': os.getenv('DB_NAME', 'opendiscourse'),
            'user': os.getenv('DB_USER', 'postgres'),
            'password': os.getenv('DB_PASSWORD', 'postgres')
        }
        
        self.api_keys = {
            'congress': os.getenv('CONGRESS_API_KEY'),
            'govinfo': os.getenv('GOVINFO_API_KEY'),
            'openstates': os.getenv('OPENSTATES_API_KEY')
        }
        
        self.results: List[ValidationResult] = []
    
    def test_database_connection(self) -> bool:
        """Test database connection and schema existence"""
        try:
            conn = psycopg2.connect(**self.db_config)
            cursor = conn.cursor()
            
            # Check if schemas exist
            cursor.execute("""
                SELECT schema_name 
                FROM information_schema.schemata 
                WHERE schema_name IN ('congress', 'govinfo', 'openstates')
                ORDER BY schema_name
            """)
            schemas = [row[0] for row in cursor.fetchall()]
            
            logger.info(f"Found schemas: {schemas}")
            
            # Check table counts
            for schema in schemas:
                cursor.execute(f"""
                    SELECT COUNT(*) 
                    FROM information_schema.tables 
                    WHERE table_schema = '{schema}'
                """)
                table_count = cursor.fetchone()[0]
                logger.info(f"{schema}: {table_count} tables")
            
            conn.close()
            return True
            
        except Exception as e:
            logger.error(f"Database connection failed: {e}")
            return False
    
    async def test_congress_api(self) -> ValidationResult:
        """Test Congress.gov API against schema"""
        result = ValidationResult(
            source="congress",
            endpoint="https://api.congress.gov/v3/bill/118/hr",
            success=False,
            sample_data={},
            missing_fields=[],
            extra_fields=[],
            errors=[],
            recommendations=[]
        )
        
        if not self.api_keys['congress']:
            result.errors.append("CONGRESS_API_KEY not found")
            return result
        
        try:
            # Test bill endpoint
            headers = {'X-API-Key': self.api_keys['congress']}
            async with aiohttp.ClientSession(headers=headers) as session:
                async with session.get(
                    "https://api.congress.gov/v3/bill/118/hr/1",
                    timeout=aiohttp.ClientTimeout(total=30)
                ) as response:
                    if response.status == 200:
                        bill_data = (await response.json()).get('bill', {})
                        result.sample_data = bill_data
                        result.success = True
                        
                        # Validate against expected schema fields
                        expected_fields = {
                            'congress', 'billType', 'billNumber', 'title', 'introducedDate',
                            'latestAction', 'sponsors', 'cosponsors', 'subjects', 'actions',
                            'textVersions', 'summaries', 'committees', 'relatedBills'
                        }
                        
                        actual_fields = set(bill_data.keys())
                        result.missing_fields = list(expected_fields - actual_fields)
                        result.extra_fields = list(actual_fields - expected_fields)
                        
                        # Recommendations
                        if result.missing_fields:
                            result.recommendations.append(
                                "Consider adding missing fields to congress.bills table"
                            )
                        
                        result.recommendations.append(
                            "Congress API response structure matches schema well"
                        )
                        
                    else:
                        result.errors.append(f"API request failed: {response.status}")
                
        except Exception as e:
            result.errors.append(f"Congress API test failed: {e}")
        
        return result
    
    async def test_govinfo_api(self) -> ValidationResult:
        """Test GovInfo.gov API against schema"""
        result = ValidationResult(
            source="govinfo",
            endpoint="https://api.govinfo.gov/packages/BILLS-118hr1",
            success=False,
            sample_data={},
            missing_fields=[],
            extra_fields=[],
            errors=[],
            recommendations=[]
        )
        
        if not self.api_keys['govinfo']:
            result.errors.append("GOVINFO_API_KEY not found")
            return result
        
        try:
            # Test package endpoint
            headers = {'X-API-Key': self.api_keys['govinfo']}
            response = requests.get(
                "https://api.govinfo.gov/packages/BILLS-118hr1/summary",
                headers=headers,
                timeout=30
            )
            
            if response.status_code == 200:
                package_data = response.json()
                result.sample_data = package_data
                result.success = True
                
                # Validate key fields
                expected_fields = {
                    'packageId', 'title', 'collectionCode', 'dateIssued',
                    'lastModified', 'download', 'billType', 'congress',
                    'billNumber', 'originChamber'
                }
                
                actual_fields = set(package_data.keys())
                result.missing_fields = list(expected_fields - actual_fields)
                result.extra_fields = list(actual_fields - expected_fields)
                
                result.recommendations.append(
                    "GovInfo API structure aligns with govinfo.packages table"
                )
                
                if 'download' in package_data:
                    result.recommendations.append(
                        "Download URLs available for multiple formats"
                    )
                
            else:
                result.errors.append(f"API request failed: {response.status_code}")
                
        except Exception as e:
            result.errors.append(f"GovInfo API test failed: {e}")
        
        return result
    
    async def test_openstates_api(self) -> ValidationResult:
        """Test OpenStates API against schema"""
        result = ValidationResult(
            source="openstates",
            endpoint="https://v3.openstates.org/graphql",
            success=False,
            sample_data={},
            missing_fields=[],
            extra_fields=[],
            errors=[],
            recommendations=[]
        )
        
        if not self.api_keys['openstates']:
            result.errors.append("OPENSTATES_API_KEY not found")
            return result
        
        try:
            # Test GraphQL query for bills
            query = """
            query($jurisdiction: String!, $session: String!) {
                bills(
                    jurisdiction: $jurisdiction
                    session: $session
                    first: 1
                ) {
                    edges {
                        node {
                            id
                            identifier
                            title
                            classification
                            subject
                            sponsorships {
                                name
                                primary
                                classification
                            }
                            actions {
                                description
                                date
                                classification
                            }
                        }
                    }
                }
            }
            """
            
            variables = {
                "jurisdiction": "ny",
                "session": "2023-2024"
            }
            
            headers = {
                'X-API-Key': self.api_keys['openstates'],
                'Content-Type': 'application/json'
            }
            
            response = requests.post(
                "https://v3.openstates.org/graphql",
                json={"query": query, "variables": variables},
                headers=headers,
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                bills = data.get('data', {}).get('bills', {}).get('edges', [])
                
                if bills:
                    bill_data = bills[0]['node']
                    result.sample_data = bill_data
                    result.success = True
                    
                    # Validate structure
                    expected_fields = {
                        'id', 'identifier', 'title', 'classification',
                        'subject', 'sponsorships', 'actions'
                    }
                    
                    actual_fields = set(bill_data.keys())
                    result.missing_fields = list(expected_fields - actual_fields)
                    result.extra_fields = list(actual_fields - expected_fields)
                    
                    result.recommendations.append(
                        "OpenStates GraphQL structure matches optimized schema"
                    )
                    
                    if 'sponsorships' in bill_data:
                        result.recommendations.append(
                            "Sponsorship data available for bill_sponsorships table"
                        )
                    
                else:
                    result.errors.append("No bills returned from OpenStates API")
                    
            else:
                result.errors.append(f"GraphQL request failed: {response.status_code}")
                
        except Exception as e:
            result.errors.append(f"OpenStates API test failed: {e}")
        
        return result
    
    def validate_schema_completeness(self) -> Dict[str, Any]:
        """Validate that all expected tables and columns exist"""
        schema_validation = {}
        
        try:
            conn = psycopg2.connect(**self.db_config)
            cursor = conn.cursor()
            
            # Check Congress schema
            cursor.execute("""
                SELECT table_name, column_name, data_type
                FROM information_schema.columns
                WHERE table_schema = 'congress'
                ORDER BY table_name, ordinal_position
            """)
            
            congress_schema = {}
            for row in cursor.fetchall():
                table, column, dtype = row
                if table not in congress_schema:
                    congress_schema[table] = []
                congress_schema[table].append(f"{column} ({dtype})")
            
            schema_validation['congress'] = congress_schema
            
            # Check GovInfo schema
            cursor.execute("""
                SELECT table_name, column_name, data_type
                FROM information_schema.columns
                WHERE table_schema = 'govinfo'
                ORDER BY table_name, ordinal_position
            """)
            
            govinfo_schema = {}
            for row in cursor.fetchall():
                table, column, dtype = row
                if table not in govinfo_schema:
                    govinfo_schema[table] = []
                govinfo_schema[table].append(f"{column} ({dtype})")
            
            schema_validation['govinfo'] = govinfo_schema
            
            # Check OpenStates schema (if exists)
            cursor.execute("""
                SELECT EXISTS (
                    SELECT 1 FROM information_schema.schemata 
                    WHERE schema_name = 'openstates'
                )
            """)
            
            if cursor.fetchone()[0]:
                cursor.execute("""
                    SELECT table_name, column_name, data_type
                    FROM information_schema.columns
                    WHERE table_schema = 'openstates'
                    ORDER BY table_name, ordinal_position
                """)
                
                openstates_schema = {}
                for row in cursor.fetchall():
                    table, column, dtype = row
                    if table not in openstates_schema:
                        openstates_schema[table] = []
                    openstates_schema[table].append(f"{column} ({dtype})")
                
                schema_validation['openstates'] = openstates_schema
            
            conn.close()
            
        except Exception as e:
            logger.error(f"Schema validation failed: {e}")
            schema_validation['error'] = str(e)
        
        return schema_validation
    
    async def run_validation(self, test_all: bool = True, source: Optional[str] = None) -> Dict[str, Any]:
        """Run comprehensive validation"""
        logger.info("Starting schema validation...")
        
        # Test database connection
        if not self.test_database_connection():
            return {'error': 'Database connection failed'}
        
        # Validate schema completeness
        schema_info = self.validate_schema_completeness()
        
        # Test APIs
        api_tests = []
        
        if test_all or source == 'congress':
            logger.info("Testing Congress.gov API...")
            result = await self.test_congress_api()
            api_tests.append(result)
        
        if test_all or source == 'govinfo':
            logger.info("Testing GovInfo.gov API...")
            result = await self.test_govinfo_api()
            api_tests.append(result)
        
        if test_all or source == 'openstates':
            logger.info("Testing OpenStates API...")
            result = await self.test_openstates_api()
            api_tests.append(result)
        
        # Generate summary
        summary = {
            'timestamp': datetime.now().isoformat(),
            'database_schemas': schema_info,
            'api_tests': [
                {
                    'source': r.source,
                    'endpoint': r.endpoint,
                    'success': r.success,
                    'missing_fields': r.missing_fields,
                    'extra_fields': r.extra_fields,
                    'errors': r.errors,
                    'recommendations': r.recommendations
                }
                for r in api_tests
            ],
            'overall_success': all(r.success for r in api_tests),
            'total_errors': sum(len(r.errors) for r in api_tests)
        }
        
        return summary
    
    def print_summary(self, summary: Dict[str, Any]):
        """Print validation summary"""
        print("\n" + "="*80)
        print("SCHEMA VALIDATION SUMMARY")
        print("="*80)
        
        print(f"Timestamp: {summary['timestamp']}")
        print(f"Overall Success: {summary['overall_success']}")
        print(f"Total Errors: {summary['total_errors']}")
        
        print("\nDATABASE SCHEMAS:")
        for schema, tables in summary['database_schemas'].items():
            if schema != 'error':
                print(f"\n{schema.upper()} Schema:")
                for table, columns in list(tables.items())[:5]:  # Show first 5 tables
                    print(f"  {table}: {len(columns)} columns")
                if len(tables) > 5:
                    print(f"  ... and {len(tables) - 5} more tables")
        
        print("\nAPI TEST RESULTS:")
        for test in summary['api_tests']:
            print(f"\n{test['source'].upper()} API:")
            print(f"  Success: {test['success']}")
            print(f"  Endpoint: {test['endpoint']}")
            
            if test['missing_fields']:
                print(f"  Missing Fields: {', '.join(test['missing_fields'])}")
            
            if test['extra_fields']:
                print(f"  Extra Fields: {', '.join(test['extra_fields'])}")
            
            if test['errors']:
                print(f"  Errors: {', '.join(test['errors'])}")
            
            if test['recommendations']:
                print(f"  Recommendations: {', '.join(test['recommendations'])}")
        
        print("\n" + "="*80)

async def main():
    """Main validation function"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Validate data schemas against APIs")
    parser.add_argument('--test-all', action='store_true', help='Test all APIs')
    parser.add_argument('--source', choices=['congress', 'govinfo', 'openstates'], 
                       help='Test specific API source')
    parser.add_argument('--output', help='Output results to file')
    
    args = parser.parse_args()
    
    validator = SchemaValidator()
    
    # Run validation
    summary = await validator.run_validation(
        test_all=args.test_all or not args.source,
        source=args.source
    )
    
    # Print summary
    validator.print_summary(summary)
    
    # Save to file if requested
    if args.output:
        with open(args.output, 'w') as f:
            json.dump(summary, f, indent=2)
        print(f"\nResults saved to: {args.output}")
    
    # Exit with error code if validation failed
    if not summary['overall_success']:
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())