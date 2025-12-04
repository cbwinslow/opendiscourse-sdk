#!/usr/bin/env python3
"""
GovInfo Test Suite Documentation and Coverage Reports
Comprehensive documentation for the GovInfo offset handling test suite
"""

import os
import sys
import json
import subprocess
from datetime import datetime
from typing import Dict, Any, List
import tempfile


class GovInfoTestDocumentation:
    """Generate comprehensive test documentation and coverage reports"""

    def __init__(self):
        self.test_files = [
            'tests/test_govinfo_offset_calculations.py',
            'tests/test_govinfo_pagination_logic.py',
            'tests/govinfo_checkpoint_system_tests.py',
            'tests/govinfo_rate_limiting_tests.py',
            'tests/govinfo_data_integrity_tests.py',
            'tests/govinfo_performance_tests.py',
            'tests/govinfo_e2e_integration_tests.py'
        ]
        self.documentation = {
            'generated_at': datetime.now().isoformat(),
            'test_suite': 'GovInfo Offset Handling Validation',
            'version': '1.0.0',
            'description': 'Comprehensive test suite for validating GovInfo ingestion offset handling fixes',
            'components': {},
            'coverage_analysis': {},
            'test_categories': {},
            'performance_metrics': {},
            'quality_gates': {}
        }

    def analyze_test_coverage(self) -> Dict[str, Any]:
        """Analyze test coverage for each component"""
        coverage_analysis = {}

        for test_file in self.test_files:
            if not os.path.exists(test_file):
                continue

            component_name = self._extract_component_name(test_file)
            coverage_analysis[component_name] = {
                'test_file': test_file,
                'test_count': 0,
                'test_methods': [],
                'coverage_area': '',
                'complexity_score': 0
            }

            try:
                with open(test_file, 'r') as f:
                    content = f.read()

                # Count test methods
                test_methods = [line.strip() for line in content.split('\n')
                              if line.strip().startswith('def test_')]
                coverage_analysis[component_name]['test_count'] = len(test_methods)
                coverage_analysis[component_name]['test_methods'] = test_methods

                # Determine coverage area
                if 'offset' in test_file.lower():
                    coverage_analysis[component_name]['coverage_area'] = 'Offset calculation and progression'
                elif 'pagination' in test_file.lower():
                    coverage_analysis[component_name]['coverage_area'] = 'API pagination logic and response handling'
                elif 'checkpoint' in test_file.lower():
                    coverage_analysis[component_name]['coverage_area'] = 'Checkpoint system and resume functionality'
                elif 'rate' in test_file.lower():
                    coverage_analysis[component_name]['coverage_area'] = 'Rate limiting and error recovery'
                elif 'integrity' in test_file.lower():
                    coverage_analysis[component_name]['coverage_area'] = 'Data integrity and duplicate prevention'
                elif 'performance' in test_file.lower():
                    coverage_analysis[component_name]['coverage_area'] = 'Performance and throughput validation'
                elif 'e2e' in test_file.lower():
                    coverage_analysis[component_name]['coverage_area'] = 'End-to-end integration testing'

                # Calculate complexity score (lines of test code / 10)
                lines = len(content.split('\n'))
                coverage_analysis[component_name]['complexity_score'] = min(lines // 10, 10)

            except Exception as e:
                coverage_analysis[component_name]['error'] = str(e)

        return coverage_analysis

    def _extract_component_name(self, test_file: str) -> str:
        """Extract component name from test file path"""
        basename = os.path.basename(test_file)
        name = basename.replace('test_', '').replace('tests.py', '').replace('.py', '')
        return name.replace('_', ' ').title()

    def categorize_tests(self) -> Dict[str, Any]:
        """Categorize tests by functionality"""
        test_categories = {
            'unit_tests': {
                'description': 'Individual component testing',
                'files': ['test_govinfo_offset_calculations.py', 'test_govinfo_pagination_logic.py'],
                'focus': 'Single method/function validation',
                'test_count': 0
            },
            'integration_tests': {
                'description': 'Component interaction testing',
                'files': ['govinfo_checkpoint_system_tests.py', 'govinfo_rate_limiting_tests.py', 'govinfo_data_integrity_tests.py'],
                'focus': 'Multi-component integration validation',
                'test_count': 0
            },
            'performance_tests': {
                'description': 'Performance and efficiency validation',
                'files': ['govinfo_performance_tests.py'],
                'focus': 'Throughput and resource utilization',
                'test_count': 0
            },
            'end_to_end_tests': {
                'description': 'Complete workflow validation',
                'files': ['govinfo_e2e_integration_tests.py'],
                'focus': 'Full ingestion pipeline testing',
                'test_count': 0
            }
        }

        # Count tests in each category
        for category, info in test_categories.items():
            total_tests = 0
            for test_file in info['files']:
                file_path = f'tests/{test_file}'
                if os.path.exists(file_path):
                    with open(file_path, 'r') as f:
                        content = f.read()
                        test_count = len([line for line in content.split('\n')
                                        if line.strip().startswith('def test_')])
                        total_tests += test_count
            info['test_count'] = total_tests

        return test_categories

    def define_quality_gates(self) -> Dict[str, Any]:
        """Define quality gates for the test suite"""
        quality_gates = {
            'code_coverage': {
                'minimum_threshold': 90,
                'target': 95,
                'description': 'Minimum percentage of code covered by tests'
            },
            'test_success_rate': {
                'minimum_threshold': 95,
                'target': 100,
                'description': 'Minimum percentage of tests that must pass'
            },
            'performance_thresholds': {
                'batch_processing_rate': {'minimum': 1000, 'unit': 'items/second'},
                'offset_calculation_accuracy': {'minimum': 99.9, 'unit': 'percentage'},
                'memory_usage': {'maximum': 100, 'unit': 'MB for 10K items'}
            },
            'error_handling': {
                'rate_limiting_recovery': {'required': True},
                'checkpoint_persistence': {'required': True},
                'data_integrity_validation': {'required': True}
            }
        }
        return quality_gates

    def generate_test_execution_report(self) -> Dict[str, Any]:
        """Generate test execution report"""
        execution_report = {
            'execution_environment': {
                'python_version': sys.version.split()[0],
                'platform': sys.platform,
                'test_framework': 'pytest',
                'coverage_tool': 'pytest-cov (if available)'
            },
            'test_runner': 'govinfo_test_runner.py',
            'execution_modes': {
                'development': 'Run all tests with verbose output',
                'production': 'Run subset with performance focus',
                'ci_cd': 'Run essential tests with fast execution'
            },
            'command_line_usage': {
                'basic': 'python tests/govinfo_test_runner.py',
                'verbose': 'python tests/govinfo_test_runner.py --verbose',
                'production': 'python tests/govinfo_test_runner.py --production',
                'custom_report': 'python tests/govinfo_test_runner.py --report-file custom_report.json'
            }
        }
        return execution_report

    def create_coverage_report(self) -> Dict[str, Any]:
        """Create detailed coverage report"""
        coverage_report = {
            'summary': {
                'total_test_files': len(self.test_files),
                'files_with_tests': sum(1 for f in self.test_files if os.path.exists(f)),
                'coverage_areas': [
                    'Offset Calculation Logic',
                    'API Pagination Handling',
                    'Checkpoint System',
                    'Rate Limiting',
                    'Data Integrity',
                    'Performance Characteristics',
                    'End-to-End Integration'
                ]
            },
            'component_coverage': self.analyze_test_coverage(),
            'test_categories': self.categorize_tests(),
            'quality_gates': self.define_quality_gates(),
            'execution_report': self.generate_test_execution_report()
        }
        return coverage_report

    def generate_markdown_documentation(self) -> str:
        """Generate comprehensive markdown documentation"""
        doc = f"""# GovInfo Offset Handling Test Suite Documentation

## Overview

This comprehensive test suite validates the fixes implemented for GovInfo offset handling during the data ingestion process. The tests ensure proper offset calculation, pagination logic, checkpoint system functionality, rate limiting, data integrity, and performance characteristics.

**Generated:** {self.documentation['generated_at']}
**Version:** {self.documentation['version']}
**Test Framework:** pytest

## Test Suite Components

### 1. Offset Calculation Tests (`test_govinfo_offset_calculations.py`)

**Purpose:** Validate that offset calculation uses actual items received vs batch size

**Key Test Cases:**
- ✅ Offset calculation with full batches
- ✅ Offset calculation with variable batch sizes
- ✅ Offset calculation resume from checkpoint
- ✅ Offset calculation stops correctly on no data
- ✅ Different data types consistency
- ✅ Statistics offset tracking
- ✅ Edge case single item batches
- ✅ Large gap handling

**Critical Validation Points:**
- Offset increments by items received, not batch size requested
- Proper offset progression through variable-sized API responses
- Accurate checkpoint offset tracking
- No gaps in offset sequence

### 2. Pagination Logic Tests (`test_govinfo_pagination_logic.py`)

**Purpose:** Test proper handling of variable API response sizes

**Key Test Cases:**
- ✅ API rate limit handling
- ✅ Inconsistent response sizes
- ✅ Maximum batch size limits
- ✅ API error handling
- ✅ Malformed response handling
- ✅ Session tracking
- ✅ Generator behavior
- ✅ Empty response handling
- ✅ Multi-data type consistency
- ✅ Large congress numbers

**Critical Validation Points:**
- API pagination respects actual response sizes
- Handles varying batch sizes gracefully
- Proper termination on empty responses
- Rate limiting integration

### 3. Checkpoint System Tests (`govinfo_checkpoint_system_tests.py`)

**Purpose:** Test resume functionality and data integrity

**Key Test Cases:**
- ✅ New ingestion checkpoint retrieval
- ✅ Existing offset retrieval
- ✅ Completed ingestion handling
- ✅ Disabled checkpoint behavior
- ✅ Database error handling
- ✅ Checkpoint updates
- ✅ Resume from checkpoint
- ✅ Skip completed data
- ✅ Session tracking
- ✅ Offset accuracy
- ✅ Interrupted ingestion recovery

**Critical Validation Points:**
- Accurate checkpoint state management
- Proper resume from last offset
- Data continuity across interruptions
- Session tracking integration

### 4. Rate Limiting Tests (`govinfo_rate_limiting_tests.py`)

**Purpose:** Test API call management and error recovery

**Key Test Cases:**
- ✅ Rate limiting (429) handling
- ✅ Retry logic on failures
- ✅ Max retries exhaustion
- ✅ Timeout handling
- ✅ Server error handling
- ✅ Rate limiting delays
- ✅ Disabled rate limiting
- ✅ API key inclusion
- ✅ Metadata tracking
- ✅ Database connection errors
- ✅ Error recovery continuation

**Critical Validation Points:**
- Proper rate limit handling with backoff
- Robust retry logic
- Graceful error recovery
- API key and metadata management

### 5. Data Integrity Tests (`govinfo_data_integrity_tests.py`)

**Purpose:** Ensure no gaps or duplicates in ingestion

**Key Test Cases:**
- ✅ Duplicate bill prevention
- ✅ Duplicate vote prevention
- ✅ Duplicate member prevention
- ✅ Gap detection in offset sequence
- ✅ Data continuity across checkpoints
- ✅ Bill data normalization
- ✅ Vote data normalization
- ✅ Member data normalization
- ✅ Invalid data filtering
- ✅ Date parsing edge cases
- ✅ Batch insertion consistency

**Critical Validation Points:**
- No duplicate data insertion
- Data normalization preserves integrity
- Invalid data is filtered out
- Proper upsert semantics

### 6. Performance Tests (`govinfo_performance_tests.py`)

**Purpose:** Test throughput and efficiency

**Key Test Cases:**
- ✅ Batch processing throughput
- ✅ Pagination efficiency
- ✅ Concurrent processing
- ✅ Memory efficiency
- ✅ API response time impact
- ✅ Large batch handling
- ✅ Checkpoint performance impact
- ✅ Rate limiting trade-offs
- ✅ Error recovery performance
- ✅ Realistic data sizes
- ✅ Throughput benchmarking

**Performance Benchmarks:**
- **Minimum Batch Processing:** 1000 items/second
- **Maximum Memory Growth:** 50MB for 10K items
- **Maximum Processing Time:** < 5 seconds per 1000 items

### 7. End-to-End Integration Tests (`govinfo_e2e_integration_tests.py`)

**Purpose:** Test complete ingestion workflow

**Key Test Cases:**
- ✅ Complete bills ingestion flow
- ✅ Complete votes ingestion flow
- ✅ Complete members ingestion flow
- ✅ Interruption and resume
- ✅ All data types sequential
- ✅ Error handling during ingestion
- ✅ Checkpoint session integration
- ✅ Multi-congress ingestion
- ✅ Production-like scenario
- ✅ Data validation flow
- ✅ Rate limiting integration

## Test Runner Usage

### Basic Execution
```bash
python tests/govinfo_test_runner.py
```

### Verbose Output
```bash
python tests/govinfo_test_runner.py --verbose
```

### Production Mode
```bash
python tests/govinfo_test_runner.py --production
```

### Custom Report
```bash
python tests/govinfo_test_runner.py --report-file my_report.json
```

### Skip Performance Tests
```bash
python tests/govinfo_test_runner.py --skip-performance
```

## Quality Gates

### Code Coverage
- **Minimum Threshold:** 90%
- **Target:** 95%

### Test Success Rate
- **Minimum Threshold:** 95%
- **Target:** 100%

### Performance Requirements
- **Batch Processing Rate:** ≥ 1000 items/second
- **Offset Calculation Accuracy:** ≥ 99.9%
- **Memory Usage:** ≤ 100MB for 10K items

## Test Categories

| Category | Focus | Files | Approx. Tests |
|----------|--------|-------|---------------|
| **Unit Tests** | Single component validation | 2 files | 20+ tests |
| **Integration Tests** | Multi-component integration | 3 files | 25+ tests |
| **Performance Tests** | Throughput and efficiency | 1 file | 10+ tests |
| **E2E Tests** | Complete workflow | 1 file | 15+ tests |
| **Total** | **Comprehensive coverage** | **7 files** | **70+ tests** |

## Coverage Areas

1. **Offset Calculation Logic** - Core offset progression validation
2. **API Pagination Handling** - Response size variation management
3. **Checkpoint System** - Resume functionality and state management
4. **Rate Limiting** - API call management and error recovery
5. **Data Integrity** - Duplicate prevention and normalization
6. **Performance Characteristics** - Throughput and resource utilization
7. **End-to-End Integration** - Complete ingestion pipeline validation

## Critical Fixes Validated

### 1. Offset Calculation Fix
**Issue:** Offset calculation used batch size instead of actual items received
**Fix:** Modified to use `len(items_received)` for offset calculation
**Validation:** Tests verify offset advances by actual API response size

### 2. Pagination Logic Fix
**Issue:** Variable API response sizes caused pagination errors
**Fix:** Enhanced pagination logic to handle varying response sizes
**Validation:** Tests simulate realistic API response variations

### 3. Checkpoint System Enhancement
**Issue:** Resume functionality had gaps and inconsistencies
**Fix:** Improved checkpoint state management and offset tracking
**Validation:** Tests verify data continuity across interruptions

### 4. Rate Limiting Integration
**Issue:** Poor handling of API rate limits and errors
**Fix:** Added adaptive rate limiting and robust retry logic
**Validation:** Tests simulate various error conditions

### 5. Data Integrity Protection
**Issue:** Potential duplicate data and validation gaps
**Fix:** Enhanced duplicate detection and data normalization
**Validation:** Tests verify no duplicates and proper validation

## Troubleshooting

### Common Issues

1. **Import Errors**
   ```bash
   # Ensure dependencies are installed
   pip install pytest requests psycopg2-binary
   ```

2. **Database Connection Issues**
   ```bash
   # Check PostgreSQL connection
   export DB_NAME=your_db_name
   export DB_USER=your_db_user
   export DB_HOST=your_db_host
   ```

3. **API Key Issues**
   ```bash
   # Set API key environment variable
   export GOVINFO_API_KEY=your_api_key
   ```

### Test Failures

- **Offset Calculation Failures:** Check API response handling logic
- **Checkpoint Failures:** Verify database schema and permissions
- **Performance Failures:** Consider adjusting test environment resources
- **Integration Failures:** Check component interaction interfaces

## CI/CD Integration

### GitHub Actions Example
```yaml
name: GovInfo Tests
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Set up Python
        uses: actions/setup-python@v2
        with:
          python-version: '3.8'
      - name: Install dependencies
        run: |
          pip install -r requirements.txt
          pip install pytest requests psycopg2-binary
      - name: Run GovInfo tests
        run: python tests/govinfo_test_runner.py --production
      - name: Upload coverage report
        uses: codecov/codecov-action@v1
```

## Reporting

The test runner generates detailed reports including:

- **JSON Report:** Complete test results with metrics
- **Console Output:** Real-time test execution feedback
- **Log Files:** Detailed execution logs (`govinfo_test_runner.log`)
- **Performance Metrics:** Throughput and efficiency measurements
- **Quality Gate Results:** Pass/fail status for each requirement

## Conclusion

This comprehensive test suite validates all critical aspects of the GovInfo offset handling fixes. The tests ensure that the ingestion process handles real-world conditions including variable API response sizes, rate limiting, checkpoint recovery, and data integrity requirements.

The test suite can be used for:
- ✅ Validation before production deployment
- ✅ Regression testing during updates
- ✅ Performance monitoring
- ✅ Quality assurance gates
- ✅ Developer testing and debugging

For questions or issues, refer to the individual test files or the test runner documentation.
"""
        return doc

    def save_documentation(self, output_file: str = None):
        """Save documentation to file"""
        if output_file is None:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            output_file = f'govinfo_test_documentation_{timestamp}.md'

        # Generate all documentation components
        self.documentation['coverage_analysis'] = self.create_coverage_report()

        # Save markdown documentation
        markdown_doc = self.generate_markdown_documentation()
        with open(output_file, 'w') as f:
            f.write(markdown_doc)

        # Save JSON analysis
        json_file = output_file.replace('.md', '_analysis.json')
        with open(json_file, 'w') as f:
            json.dump(self.documentation, f, indent=2)

        print(f"📄 Documentation saved to: {output_file}")
        print(f"📊 Analysis saved to: {json_file}")

        return output_file, json_file


def main():
    """Generate documentation and coverage reports"""
    print("🔧 Generating GovInfo Test Suite Documentation...")

    try:
        doc_generator = GovInfoTestDocumentation()
        output_file, json_file = doc_generator.save_documentation()

        print("✅ Documentation generation complete!")
        print(f"📄 Markdown: {output_file}")
        print(f"📊 JSON Analysis: {json_file}")

        # Print summary
        coverage = doc_generator.create_coverage_report()
        print("\n📈 Coverage Summary:")
        print(f"  Test Files: {coverage['summary']['total_test_files']}")
        print(f"  Files with Tests: {coverage['summary']['files_with_tests']}")
        print(f"  Coverage Areas: {len(coverage['summary']['coverage_areas'])}")

        categories = coverage['test_categories']
        print(f"\n🧪 Test Categories:")
        for category, info in categories.items():
            print(f"  • {category}: {info['test_count']} tests")

    except Exception as e:
        print(f"❌ Documentation generation failed: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()
