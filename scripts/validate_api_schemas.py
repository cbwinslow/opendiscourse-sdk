#!/usr/bin/env python3
"""
API Schema Validation Script
Tests API responses against expected data model structures
Validates that our schemas can handle real API data

Usage:
    python validate_api_schemas.py [--source congress|govinfo|openstates]
"""

import os
import json
import requests
from typing import Dict, List, Any, Optional
from datetime import datetime
from dataclasses import dataclass
from pathlib import Path

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

@dataclass
class APIValidationResult:
    """API validation result"""
    source: str
    endpoint: str
    success: bool
    sample_data: Dict[str, Any]
    schema_compatibility: str
    missing_fields: List[str]
    recommendations: List[str]

class APISchemaValidator:
    """API-only schema validation"""
    
    def __init__(self):
        self.api_keys = {
            'congress': os.getenv('CONGRESS_API_KEY'),
            'govinfo': os.getenv('GOVINFO_API_KEY'),
            'openstates': os.getenv('OPENSTATES_API_KEY')
        }
        
        # Expected schema structures for validation
        self.expected_structures = {
            'congress': {
                'bill': {
                    'required': ['congress', 'billType', 'billNumber', 'title'],
                    'recommended': ['introducedDate', 'latestAction', 'sponsors', 'actions'],
                    'maps_to': ['congress.bills', 'congress.bill_actions', 'congress.bill_sponsors']
                },
                'member': {
                    'required': ['bioguideId', 'firstName', 'lastName', 'party'],
                    'recommended': ['state', 'district', 'terms'],
                    'maps_to': ['congress.members', 'congress.member_terms']
                }
            },
            'govinfo': {
                'package': {
                    'required': ['packageId', 'title', 'collectionCode'],
                    'recommended': ['dateIssued', 'download', 'congress', 'billType'],
                    'maps_to': ['govinfo.packages', 'govinfo.bills']
                },
                'collection': {
                    'required': ['collectionCode', 'collectionName'],
                    'recommended': ['packageCount', 'granuleCount'],
                    'maps_to': ['govinfo.collections']
                }
            },
            'openstates': {
                'bill': {
                    'required': ['id', 'identifier', 'title', 'jurisdiction'],
                    'recommended': ['sponsorships', 'actions', 'subjects'],
                    'maps_to': ['openstates.bills', 'openstates.bill_sponsorships', 'openstates.bill_actions']
                },
                'jurisdiction': {
                    'required': ['id', 'name', 'classification'],
                    'recommended': ['url', 'latestBillUpdate'],
                    'maps_to': ['openstates.jurisdictions']
                }
            }
        }
    
    def test_congress_api(self) -> APIValidationResult:
        """Test Congress.gov API"""
        result = APIValidationResult(
            source="congress",
            endpoint="https://api.congress.gov/v3/bill",
            success=False,
            sample_data={},
            schema_compatibility="unknown",
            missing_fields=[],
            recommendations=[]
        )
        
        if not self.api_keys['congress']:
            result.recommendations.append("Add CONGRESS_API_KEY to .env file")
            return result
        
        try:
            headers = {'X-API-Key': self.api_keys['congress']}
            
            # Test bill endpoint
            response = requests.get(
                "https://api.congress.gov/v3/bill/118/hr/1",
                headers=headers,
                timeout=30
            )
            
            if response.status_code == 200:
                bill_data = response.json().get('bill', {})
                result.sample_data = {'bill': bill_data}
                result.success = True
                
                # Validate structure
                expected = self.expected_structures['congress']['bill']
                actual_fields = set(bill_data.keys())
                
                missing = set(expected['required']) - actual_fields
                result.missing_fields = list(missing)
                
                if not missing:
                    result.schema_compatibility = "excellent"
                    result.recommendations.append(
                        "Congress API structure matches schema perfectly"
                    )
                else:
                    result.schema_compatibility = "good"
                    result.recommendations.append(
                        f"Consider handling missing fields: {', '.join(missing)}"
                    )
                
                # Check nested structures
                if 'sponsors' in bill_data:
                    result.recommendations.append(
                        "Sponsor data available for congress.bill_sponsors table"
                    )
                
                if 'actions' in bill_data:
                    result.recommendations.append(
                        "Action data available for congress.bill_actions table"
                    )
                
            else:
                result.schema_compatibility = "poor"
                result.recommendations.append(f"API request failed: {response.status_code}")
                
        except Exception as e:
            result.schema_compatibility = "error"
            result.recommendations.append(f"Congress API test failed: {e}")
        
        return result
    
    def test_govinfo_api(self) -> APIValidationResult:
        """Test GovInfo.gov API"""
        result = APIValidationResult(
            source="govinfo",
            endpoint="https://api.govinfo.gov/packages",
            success=False,
            sample_data={},
            schema_compatibility="unknown",
            missing_fields=[],
            recommendations=[]
        )
        
        if not self.api_keys['govinfo']:
            result.recommendations.append("Add GOVINFO_API_KEY to .env file")
            return result
        
        try:
            headers = {'X-API-Key': self.api_keys['govinfo']}
            
            # Test package endpoint
            response = requests.get(
                "https://api.govinfo.gov/packages/BILLS-118hr1/summary",
                headers=headers,
                timeout=30
            )
            
            if response.status_code == 200:
                package_data = response.json()
                result.sample_data = {'package': package_data}
                result.success = True
                
                # Validate structure
                expected = self.expected_structures['govinfo']['package']
                actual_fields = set(package_data.keys())
                
                missing = set(expected['required']) - actual_fields
                result.missing_fields = list(missing)
                
                if not missing:
                    result.schema_compatibility = "excellent"
                    result.recommendations.append(
                        "GovInfo API structure matches schema perfectly"
                    )
                else:
                    result.schema_compatibility = "good"
                    result.recommendations.append(
                        f"Consider handling missing fields: {', '.join(missing)}"
                    )
                
                # Check bill-specific fields
                if 'billType' in package_data and 'congress' in package_data:
                    result.recommendations.append(
                        "Bill metadata available for govinfo.bills table"
                    )
                
                if 'download' in package_data:
                    result.recommendations.append(
                        "Multiple download formats available"
                    )
                
            else:
                result.schema_compatibility = "poor"
                result.recommendations.append(f"API request failed: {response.status_code}")
                
        except Exception as e:
            result.schema_compatibility = "error"
            result.recommendations.append(f"GovInfo API test failed: {e}")
        
        return result
    
    def test_openstates_api(self) -> APIValidationResult:
        """Test OpenStates API"""
        result = APIValidationResult(
            source="openstates",
            endpoint="https://v3.openstates.org/graphql",
            success=False,
            sample_data={},
            schema_compatibility="unknown",
            missing_fields=[],
            recommendations=[]
        )
        
        if not self.api_keys['openstates']:
            result.recommendations.append("Add OPENSTATES_API_KEY to .env file")
            return result
        
        try:
            # Test GraphQL query
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
                    result.sample_data = {'bill': bill_data}
                    result.success = True
                    
                    # Validate structure
                    expected = self.expected_structures['openstates']['bill']
                    actual_fields = set(bill_data.keys())
                    
                    missing = set(expected['required']) - actual_fields
                    result.missing_fields = list(missing)
                    
                    if not missing:
                        result.schema_compatibility = "excellent"
                        result.recommendations.append(
                            "OpenStates API structure matches optimized schema perfectly"
                        )
                    else:
                        result.schema_compatibility = "good"
                        result.recommendations.append(
                            f"Consider handling missing fields: {', '.join(missing)}"
                        )
                    
                    # Check nested structures
                    if 'sponsorships' in bill_data:
                        result.recommendations.append(
                            "Sponsorship data available for openstates.bill_sponsorships table"
                        )
                    
                    if 'actions' in bill_data:
                        result.recommendations.append(
                            "Action data available for openstates.bill_actions table"
                        )
                    
                    if 'subject' in bill_data:
                        result.recommendations.append(
                            "Subject data available for policy analysis"
                        )
                    
                else:
                    result.schema_compatibility = "fair"
                    result.recommendations.append("No bills returned - may need different jurisdiction/session")
                    
            else:
                result.schema_compatibility = "poor"
                result.recommendations.append(f"GraphQL request failed: {response.status_code}")
                
        except Exception as e:
            result.schema_compatibility = "error"
            result.recommendations.append(f"OpenStates API test failed: {e}")
        
        return result
    
    def validate_all(self, source: Optional[str] = None) -> List[APIValidationResult]:
        """Run all validations"""
        results = []
        
        if not source or source == 'congress':
            print("Testing Congress.gov API...")
            results.append(self.test_congress_api())
        
        if not source or source == 'govinfo':
            print("Testing GovInfo.gov API...")
            results.append(self.test_govinfo_api())
        
        if not source or source == 'openstates':
            print("Testing OpenStates API...")
            results.append(self.test_openstates_api())
        
        return results
    
    def print_results(self, results: List[APIValidationResult]):
        """Print validation results"""
        print("\n" + "="*80)
        print("API SCHEMA VALIDATION RESULTS")
        print("="*80)
        print(f"Timestamp: {datetime.now().isoformat()}")
        
        for result in results:
            print(f"\n{result.source.upper()} API:")
            print(f"  Endpoint: {result.endpoint}")
            print(f"  Success: {result.success}")
            print(f"  Schema Compatibility: {result.schema_compatibility}")
            
            if result.sample_data:
                data_keys = list(result.sample_data.keys())
                print(f"  Data Types: {', '.join(data_keys)}")
                
                # Show sample structure
                for data_type, data in result.sample_data.items():
                    if isinstance(data, dict):
                        print(f"  {data_type.title()} Fields: {', '.join(list(data.keys())[:5])}...")
            
            if result.missing_fields:
                print(f"  Missing Required Fields: {', '.join(result.missing_fields)}")
            
            if result.recommendations:
                print("  Recommendations:")
                for rec in result.recommendations:
                    print(f"    • {rec}")
        
        # Overall summary
        success_count = sum(1 for r in results if r.success)
        total_count = len(results)
        
        print(f"\nOVERALL SUMMARY:")
        print(f"  Successful Tests: {success_count}/{total_count}")
        print(f"  Success Rate: {success_count/total_count*100:.1f}%")
        
        if success_count == total_count:
            print("  ✅ All APIs are accessible and compatible with your schemas!")
        else:
            print("  ⚠️  Some API tests failed - check recommendations above")
        
        print("\n" + "="*80)

def main():
    """Main validation function"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Validate API schemas")
    parser.add_argument('--source', choices=['congress', 'govinfo', 'openstates'], 
                       help='Test specific API source')
    parser.add_argument('--output', help='Save results to JSON file')
    
    args = parser.parse_args()
    
    validator = APISchemaValidator()
    results = validator.validate_all(args.source)
    
    # Print results
    validator.print_results(results)
    
    # Save to file if requested
    if args.output:
        output_data = {
            'timestamp': datetime.now().isoformat(),
            'results': [
                {
                    'source': r.source,
                    'endpoint': r.endpoint,
                    'success': r.success,
                    'schema_compatibility': r.schema_compatibility,
                    'missing_fields': r.missing_fields,
                    'recommendations': r.recommendations,
                    'sample_data_keys': list(r.sample_data.keys()) if r.sample_data else []
                }
                for r in results
            ]
        }
        
        with open(args.output, 'w') as f:
            json.dump(output_data, f, indent=2)
        
        print(f"\nResults saved to: {args.output}")

if __name__ == "__main__":
    main()