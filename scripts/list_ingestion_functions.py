#!/usr/bin/env python3
"""
Function Listing Script for OpenDiscourse Data Ingestion
Lists all available functions and their descriptions from the comprehensive data ingestion script
"""

import inspect
import sys
import os
import argparse
from typing import Dict, List, Any
import textwrap
import json
import yaml
from datetime import datetime

# Add scripts directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__)))

try:
    from comprehensive_data_ingestion import DataIngestionManager, IngestionConfig, IngestionResult
    import comprehensive_data_ingestion as ingestion_module
except ImportError as e:
    print(f"❌ Error importing comprehensive_data_ingestion: {e}")
    sys.exit(1)

def get_function_info(func) -> Dict[str, Any]:
    """Extract information about a function"""
    try:
        # Get function signature
        sig = inspect.signature(func)
        params = []
        for name, param in sig.parameters.items():
            param_info = {
                'name': name,
                'type': str(param.annotation) if param.annotation != inspect.Parameter.empty else 'Any',
                'default': param.default if param.default != inspect.Parameter.empty else None
            }
            params.append(param_info)

        # Get docstring
        docstring = func.__doc__ or "No documentation available"
        doc_lines = [line.strip() for line in docstring.strip().split('\n') if line.strip()]

        # Extract first line as description
        description = doc_lines[0] if doc_lines else "No description available"
        details = doc_lines[1:] if len(doc_lines) > 1 else []

        return {
            'name': func.__name__,
            'description': description,
            'details': details,
            'parameters': params,
            'return_type': str(sig.return_annotation) if sig.return_annotation != sig.empty else 'Any',
            'module': func.__module__,
            'is_method': hasattr(func, '__self__') and func.__self__ is not None
        }
    except Exception as e:
        print(f"⚠️  Warning: Could not extract info for {func.__name__ if hasattr(func, '__name__') else 'unknown'}: {e}")
        return {
            'name': getattr(func, '__name__', 'unknown'),
            'description': "Could not extract function information",
            'details': [],
            'parameters': [],
            'return_type': 'Unknown',
            'module': getattr(func, '__module__', 'unknown'),
            'is_method': False
        }

def list_class_methods(cls) -> List[Dict[str, Any]]:
    """List all methods of a class"""
    methods = []
    for name, method in inspect.getmembers(cls, inspect.isfunction):
        if name.startswith('_') and not name.startswith('__'):
            continue  # Skip private methods but keep dunder methods
        methods.append(get_function_info(method))
    return methods

def list_module_functions(module) -> List[Dict[str, Any]]:
    """List all functions in a module"""
    functions = []
    for name, obj in inspect.getmembers(module):
        if inspect.isfunction(obj) and not name.startswith('_'):
            functions.append(get_function_info(obj))
    return functions

def generate_function_documentation() -> Dict[str, Any]:
    """Generate comprehensive function documentation"""
    documentation = {
        'generated_at': datetime.now().isoformat(),
        'module': 'comprehensive_data_ingestion',
        'classes': [],
        'functions': [],
        'summary': {
            'total_classes': 0,
            'total_methods': 0,
            'total_functions': 0,
            'total_documented': 0
        }
    }

    # Document classes
    classes = [DataIngestionManager, IngestionConfig, IngestionResult]
    for cls in classes:
        class_doc = {
            'name': cls.__name__,
            'description': cls.__doc__ or "No description available",
            'methods': list_class_methods(cls)
        }
        documentation['classes'].append(class_doc)
        documentation['summary']['total_classes'] += 1
        documentation['summary']['total_methods'] += len(class_doc['methods'])

    # Document module functions
    module_functions = list_module_functions(ingestion_module)
    documentation['functions'] = module_functions
    documentation['summary']['total_functions'] = len(module_functions)

    # Calculate documented count
    total_methods = sum(len(cls['methods']) for cls in documentation['classes'])
    total_functions = len(documentation['functions'])
    documentation['summary']['total_documented'] = total_methods + total_functions

    return documentation

def print_function_listing(documentation: Dict[str, Any]):
    """Print function listing in a readable format"""
    print("📋 COMPREHENSIVE DATA INGESTION FUNCTION LISTING")
    print("=" * 80)
    print(f"📅 Generated: {documentation['generated_at']}")
    print(f"📊 Total Functions: {documentation['summary']['total_documented']}")
    print(f"📋 Classes: {documentation['summary']['total_classes']}")
    print(f"🔧 Methods: {documentation['summary']['total_methods']}")
    print(f"📝 Functions: {documentation['summary']['total_functions']}")
    print()

    # Print classes and their methods
    for class_doc in documentation['classes']:
        print(f"🔷 CLASS: {class_doc['name']}")
        print(f"   {class_doc['description']}")
        print()

        for method in class_doc['methods']:
            print(f"   🔹 {method['name']}({', '.join(p['name'] for p in method['parameters'])})")
            print(f"      {method['description']}")

            if method['details']:
                print("      Details:")
                for detail in method['details']:
                    print(f"        • {detail}")

            print()

    # Print module functions
    print("📋 MODULE FUNCTIONS:")
    for func in documentation['functions']:
        print(f"   🔹 {func['name']}({', '.join(p['name'] for p in func['parameters'])})")
        print(f"      {func['description']}")

        if func['details']:
            print("      Details:")
            for detail in func['details']:
                print(f"        • {detail}")

        print()

def save_documentation(documentation: Dict[str, Any], format: str = 'json') -> bool:
    """Save function documentation to file"""
    try:
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"function_documentation_{timestamp}.{format}"
        filepath = os.path.join('docs', filename)

        os.makedirs('docs', exist_ok=True)

        if format == 'json':
            with open(filepath, 'w') as f:
                json.dump(documentation, f, indent=2, default=str)
        elif format == 'yaml':
            with open(filepath, 'w') as f:
                yaml.dump(documentation, f, default_flow_style=False, sort_keys=False)
        elif format == 'md':
            with open(filepath, 'w') as f:
                f.write("# Comprehensive Data Ingestion Function Documentation\n\n")
                f.write(f"Generated: {documentation['generated_at']}\n\n")

                # Write summary
                f.write("## Summary\n\n")
                f.write(f"- Total Classes: {documentation['summary']['total_classes']}\n")
                f.write(f"- Total Methods: {documentation['summary']['total_methods']}\n")
                f.write(f"- Total Functions: {documentation['summary']['total_functions']}\n")
                f.write(f"- Total Documented: {documentation['summary']['total_documented']}\n\n")

                # Write classes
                for class_doc in documentation['classes']:
                    f.write(f"## {class_doc['name']}\n\n")
                    f.write(f"{class_doc['description']}\n\n")

                    for method in class_doc['methods']:
                        f.write(f"### {method['name']}\n\n")
                        f.write(f"**Signature:** `{method['name']}({', '.join(f'{p['name']}: {p['type']}' for p in method['parameters'])}) -> {method['return_type']}`\n\n")
                        f.write(f"**Description:** {method['description']}\n\n")

                        if method['details']:
                            f.write("**Details:**\n\n")
                            for detail in method['details']:
                                f.write(f"- {detail}\n")
                            f.write("\n")

                # Write functions
                f.write("## Module Functions\n\n")
                for func in documentation['functions']:
                    f.write(f"### {func['name']}\n\n")
                    f.write(f"**Signature:** `{func['name']}({', '.join(f'{p['name']}: {p['type']}' for p in func['parameters'])}) -> {func['return_type']}`\n\n")
                    f.write(f"**Description:** {func['description']}\n\n")

                    if func['details']:
                        f.write("**Details:**\n\n")
                        for detail in func['details']:
                            f.write(f"- {detail}\n")
                        f.write("\n")

        print(f"✅ Documentation saved to {filepath}")
        return True
    except Exception as e:
        print(f"❌ Failed to save documentation: {e}")
        return False

def main():
    """Main function"""
    parser = argparse.ArgumentParser(description='List all functions in OpenDiscourse Data Ingestion')
    parser.add_argument('--format', choices=['json', 'yaml', 'md'], default='md',
                       help='Output format for documentation')
    parser.add_argument('--save', action='store_true', help='Save documentation to file')
    parser.add_argument('--verbose', action='store_true', help='Verbose output')

    args = parser.parse_args()

    try:
        # Generate function documentation
        documentation = generate_function_documentation()

        # Print function listing
        print_function_listing(documentation)

        # Save documentation if requested
        if args.save:
            save_documentation(documentation, format=args.format)

        # Print quick reference
        print("🚀 QUICK REFERENCE GUIDE")
        print("=" * 80)
        print("USAGE EXAMPLES:")
        print()
        print("1. Ingest Congress data:")
        print("   python comprehensive_data_ingestion.py --source congress --congress 118")
        print()
        print("2. Ingest GovInfo data:")
        print("   python comprehensive_data_ingestion.py --source govinfo --collection BILLS --year 2023")
        print()
        print("3. Ingest OpenStates data:")
        print("   python comprehensive_data_ingestion.py --source openstates --state CA")
        print()
        print("4. Run comprehensive ingestion:")
        print("   python comprehensive_data_ingestion.py --source all")
        print()
        print("5. List all functions:")
        print("   python list_ingestion_functions.py")
        print()
        print("📚 DOCUMENTATION:")
        print("   • Full API documentation available in docs/")
        print("   • Configuration: ingestion_config.yaml")
        print("   • Environment variables: .env file")
        print("   • Database: PostgreSQL connection string")
        print()
        print("🎯 KEY FEATURES:")
        print("   • Multi-source data ingestion (Congress, GovInfo, OpenStates)")
        print("   • Parallel processing with ThreadPoolExecutor")
        print("   • Comprehensive error handling and retry logic")
        print("   • Database integration with PostgreSQL")
        print("   • File-based backup and recovery")
        print("   • Detailed reporting and analytics")
        print("   • Configuration management")
        print("   • CLI interface with flexible options")

    except Exception as e:
        print(f"❌ Error generating function documentation: {e}")
        return 1

    return 0

if __name__ == "__main__":
    sys.exit(main())
