#!/usr/bin/env python3
"""
Integration tests for Auto Issue Creator

This file contains example tests that could be run to verify
the auto issue creator functionality. These are not executed
automatically but can be used for manual testing.
"""

import os
import sys
from pathlib import Path


def test_yaml_syntax():
    """Test that workflow YAML files have valid syntax."""
    import yaml
    
    workflow_files = [
        '.github/workflows/auto-issue-creator.yml',
        '.github/workflows/deploy-multi-repo-scanner.yml'
    ]
    
    print("Testing YAML syntax...")
    for file_path in workflow_files:
        try:
            with open(file_path) as f:
                yaml.safe_load(f)
            print(f"  ✅ {file_path} - Valid YAML")
        except Exception as e:
            print(f"  ❌ {file_path} - Error: {e}")
            return False
    
    return True


def test_python_syntax():
    """Test that Python scripts have valid syntax."""
    import ast
    
    script_files = [
        '.github/scripts/scan_repository_errors.py'
    ]
    
    print("\nTesting Python syntax...")
    for file_path in script_files:
        try:
            with open(file_path) as f:
                ast.parse(f.read())
            print(f"  ✅ {file_path} - Valid Python")
        except Exception as e:
            print(f"  ❌ {file_path} - Error: {e}")
            return False
    
    return True


def test_scanner_patterns():
    """Test that TODO/FIXME pattern matching works."""
    import re
    
    print("\nTesting TODO/FIXME patterns...")
    
    patterns = [
        (r'#\s*(TODO|FIXME|HACK|XXX|BUG)[\s:]+(.+)', ['.py']),
        (r'//\s*(TODO|FIXME|HACK|XXX|BUG)[\s:]+(.+)', ['.js', '.ts']),
        (r'/\*\s*(TODO|FIXME|HACK|XXX|BUG)[\s:]+(.+?)\*/', ['.js', '.css']),
    ]
    
    test_cases = [
        ("# TODO: Fix this", "TODO", "Fix this"),
        ("// FIXME: Refactor", "FIXME", "Refactor"),
        ("/* BUG: Handle error */", "BUG", "Handle error"),
    ]
    
    for text, expected_type, expected_msg in test_cases:
        matched = False
        for pattern, _ in patterns:
            match = re.search(pattern, text)
            if match:
                matched = True
                if match.group(1) == expected_type and expected_msg in match.group(2):
                    print(f"  ✅ Pattern matched: {text}")
                else:
                    print(f"  ❌ Pattern match failed: {text}")
                    return False
                break
        
        if not matched:
            print(f"  ❌ No pattern matched: {text}")
            return False
    
    return True


def test_documentation_exists():
    """Test that all documentation files exist."""
    print("\nTesting documentation files...")
    
    doc_files = [
        '.github/workflows/AUTO_ISSUE_CREATOR_README.md',
        '.github/workflows/QUICK_START_GUIDE.md',
        '.github/workflows/CONFIG.md',
        '.github/workflows/VISUAL_EXAMPLES.md',
        'AUTO_ISSUE_CREATOR_SUMMARY.md',
    ]
    
    for file_path in doc_files:
        if Path(file_path).exists():
            print(f"  ✅ {file_path} - Exists")
        else:
            print(f"  ❌ {file_path} - Missing")
            return False
    
    return True


def test_scanner_can_import():
    """Test that the scanner script can be imported."""
    print("\nTesting scanner import...")
    
    try:
        sys.path.insert(0, '.github/scripts')
        # Just check if it can be compiled
        import py_compile
        py_compile.compile('.github/scripts/scan_repository_errors.py', doraise=True)
        print(f"  ✅ Scanner can be compiled")
        return True
    except Exception as e:
        print(f"  ❌ Scanner import failed: {e}")
        return False


def test_workflow_permissions():
    """Test that workflows have correct permissions."""
    import yaml
    
    print("\nTesting workflow permissions...")
    
    with open('.github/workflows/auto-issue-creator.yml') as f:
        workflow = yaml.safe_load(f)
    
    permissions = workflow.get('permissions', {})
    
    required_permissions = {
        'contents': 'read',
        'issues': 'write',
        'pull-requests': 'write'
    }
    
    for perm, level in required_permissions.items():
        if permissions.get(perm) == level:
            print(f"  ✅ Permission '{perm}': {level}")
        else:
            print(f"  ❌ Permission '{perm}' not set correctly")
            return False
    
    return True


def test_workflow_triggers():
    """Test that workflows have expected triggers."""
    import yaml
    
    print("\nTesting workflow triggers...")
    
    with open('.github/workflows/auto-issue-creator.yml') as f:
        workflow = yaml.safe_load(f)
    
    # In YAML, 'on' is parsed as boolean True
    on_config = workflow.get(True, workflow.get('on', {}))
    
    if isinstance(on_config, str):
        print(f"  ℹ️  Simple trigger: {on_config}")
        return True
    
    if not isinstance(on_config, dict):
        print(f"  ❌ No trigger configuration found")
        return False
    
    required_triggers = ['workflow_run', 'issue_comment', 'pull_request', 'schedule', 'workflow_dispatch']
    
    found_triggers = []
    for trigger in required_triggers:
        if trigger in on_config:
            print(f"  ✅ Trigger '{trigger}' configured")
            found_triggers.append(trigger)
    
    if len(found_triggers) >= 3:  # At least 3 triggers should be present
        return True
    else:
        print(f"  ❌ Expected at least 3 triggers, found {len(found_triggers)}")
        return False


def run_all_tests():
    """Run all tests."""
    print("=" * 60)
    print("Auto Issue Creator - Integration Tests")
    print("=" * 60)
    
    tests = [
        test_yaml_syntax,
        test_python_syntax,
        test_scanner_patterns,
        test_documentation_exists,
        test_scanner_can_import,
        test_workflow_permissions,
        test_workflow_triggers,
    ]
    
    results = []
    for test in tests:
        try:
            result = test()
            results.append((test.__name__, result))
        except Exception as e:
            print(f"\n❌ Test {test.__name__} failed with exception: {e}")
            results.append((test.__name__, False))
    
    print("\n" + "=" * 60)
    print("Test Results Summary")
    print("=" * 60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} - {test_name}")
    
    print("=" * 60)
    print(f"Results: {passed}/{total} tests passed")
    print("=" * 60)
    
    return all(result for _, result in results)


if __name__ == '__main__':
    # Change to repository root if needed
    if not Path('.github').exists():
        print("❌ Must be run from repository root")
        sys.exit(1)
    
    success = run_all_tests()
    sys.exit(0 if success else 1)
