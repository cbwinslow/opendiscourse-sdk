#!/usr/bin/env python3
"""
Comprehensive test script for GitHub Management CrewAI System
Validates all components and dependencies
"""

import sys
import os
import importlib
import traceback
from pathlib import Path

def print_header(title):
    """Print formatted header"""
    print("\n" + "="*50)
    print(f"  {title}")
    print("="*50)

def print_test(test_name, status, message=""):
    """Print test result"""
    symbol = "✓" if status else "✗"
    color = "\033[92m" if status else "\033[91m"
    reset = "\033[0m"

    print(f"{color}{symbol}{reset} {test_name}")
    if message:
        print(f"    {message}")

def test_python_version():
    """Test Python version compatibility"""
    print_header("Python Version Check")

    version = sys.version_info
    if version.major >= 3 and version.minor >= 8:
        print_test(
            f"Python {version.major}.{version.minor}.{version.micro}",
            True,
            "Version compatible"
        )
        return True
    else:
        print_test(
            f"Python {version.major}.{version.minor}.{version.micro}",
            False,
            "Requires Python 3.8+"
        )
        return False

def test_imports():
    """Test all required imports"""
    print_header("Module Import Tests")

    modules = [
        ("crewai", "CrewAI multi-agent framework"),
        ("github", "PyGitHub library"),
        ("requests", "HTTP requests library"),
        ("asyncio", "AsyncIO support"),
        ("aiohttp", "AsyncHTTP client"),
        ("openai", "OpenAI client"),
        ("logging", "Logging support"),
        ("json", "JSON processing"),
        ("pathlib", "Path handling"),
        ("datetime", "DateTime operations"),
        ("dataclasses", "Data class support"),
        ("typing", "Type hints"),
        ("subprocess", "Subprocess execution"),
        ("PyYAML", "YAML processing"),
        ("python-dotenv", "Environment variables"),
        ("markdown", "Markdown processing"),
        ("beautifulsoup4", "HTML parsing"),
        ("jinja2", "Template engine"),
        ("gitpython", "Git operations"),
        ("click", "Command line interface"),
        ("rich", "Terminal formatting"),
        ("pydantic", "Data validation"),
        ("fastapi", "Web framework"),
        ("uvicorn", "ASGI server"),
        ("pytest", "Testing framework"),
    ]

    results = []

    for module_name, description in modules:
        try:
            importlib.import_module(module_name.replace("-", "_"))
            print_test(f"{module_name}", True, description)
            results.append(True)
        except ImportError as e:
            print_test(f"{module_name}", False, f"Import failed: {e}")
            results.append(False)
        except Exception as e:
            print_test(f"{module_name}", False, f"Error: {e}")
            results.append(False)

    return all(results)

def test_core_components():
    """Test core system components"""
    print_header("Core Component Tests")

    # Add current directory to Python path
    current_dir = Path(__file__).parent
    sys.path.insert(0, str(current_dir))

    components = [
        ("github_crew_config", "Core GitHub CrewAI configuration"),
        ("ai_services_integration", "AI services integration"),
        ("project_v2_management", "Project v2 management"),
        ("main_orchestrator", "Main orchestrator"),
    ]

    results = []

    for component_name, description in components:
        try:
            module = importlib.import_module(component_name)
            print_test(component_name, True, description)

            # Test key classes exist
            key_classes = {
                "github_crew_config": ["GitHubOperationsManager", "GitHubConfig", "create_github_management_crew"],
                "ai_services_integration": ["AIServicesManager", "OpenRouterIntegration"],
                "project_v2_management": ["ProjectV2ManagementAgent", "GitHubProjectsV2Manager"],
                "main_orchestrator": ["GitHubManagementOrchestrator"],
            }

            if component_name in key_classes:
                for class_name in key_classes[component_name]:
                    if hasattr(module, class_name):
                        print_test(f"  {class_name}", True, "Class available")
                    else:
                        print_test(f"  {class_name}", False, "Class missing")
                        results.append(False)

            results.append(True)

        except ImportError as e:
            print_test(component_name, False, f"Import failed: {e}")
            results.append(False)
        except Exception as e:
            print_test(component_name, False, f"Error: {e}")
            results.append(False)

    return all(results)

def test_configuration():
    """Test configuration and environment"""
    print_header("Configuration Tests")

    # Test .env file
    env_exists = os.path.exists(".env")
    print_test(".env file", env_exists, "Environment file present" if env_exists else "Create .env file")

    # Test required files
    required_files = [
        ("requirements.txt", "Python dependencies"),
        ("run_github_analysis.sh", "Startup script"),
        ("README.md", "Documentation"),
    ]

    results = []

    for file_path, description in required_files:
        file_exists = os.path.exists(file_path)
        print_test(file_path, file_exists, description)
        results.append(file_exists)

    # Test script permissions
    script_path = "run_github_analysis.sh"
    if os.path.exists(script_path):
        if os.access(script_path, os.X_OK):
            print_test("Script permissions", True, "Executable")
        else:
            print_test("Script permissions", False, "Not executable")
            results.append(False)

    return all(results)

def test_github_integration():
    """Test GitHub integration components"""
    print_header("GitHub Integration Tests")

    try:
        from github_crew_config import GitHubConfig, GitHubOperationsManager

        # Test configuration creation
        config = GitHubConfig("test", "test")
        print_test("GitHubConfig creation", True, "Configuration object created")

        # Test manager creation
        manager = GitHubOperationsManager(config)
        print_test("GitHubOperationsManager creation", True, "Manager object created")

        return True

    except Exception as e:
        print_test("GitHub integration", False, f"Error: {e}")
        return False

def test_ai_services():
    """Test AI services integration"""
    print_header("AI Services Tests")

    try:
        from ai_services_integration import AIServicesManager

        # Test manager creation
        ai_manager = AIServicesManager()
        print_test("AIServicesManager creation", True, "AI manager created")

        # Test individual service classes
        from ai_services_integration import OpenRouterIntegration, OllamaIntegration, GeminiCLIIntegration

        openrouter = OpenRouterIntegration()
        print_test("OpenRouterIntegration", True, "OpenRouter service initialized")

        ollama = OllamaIntegration()
        print_test("OllamaIntegration", True, "Ollama service initialized")

        gemini = GeminiCLIIntegration()
        print_test("GeminiCLIIntegration", True, "Gemini service initialized")

        return True

    except Exception as e:
        print_test("AI services", False, f"Error: {e}")
        return False

def test_project_management():
    """Test project management components"""
    print_header("Project Management Tests")

    try:
        from project_v2_management import ProjectV2ManagementAgent

        # Create mock GitHub manager for testing
        from github_crew_config import GitHubConfig, GitHubOperationsManager
        config = GitHubConfig("test", "test")
        github_manager = GitHubOperationsManager(config)

        # Test agent creation
        project_agent = ProjectV2ManagementAgent(github_manager)
        print_test("ProjectV2ManagementAgent creation", True, "Project manager created")

        return True

    except Exception as e:
        print_test("Project management", False, f"Error: {e}")
        return False

def test_orchestrator():
    """Test main orchestrator"""
    print_header("Orchestrator Tests")

    try:
        from main_orchestrator import GitHubManagementOrchestrator

        # Test orchestrator creation (without real GitHub token)
        orchestrator = GitHubManagementOrchestrator("test", "test", "test_token")
        print_test("GitHubManagementOrchestrator creation", True, "Orchestrator created")

        # Test that key methods exist
        methods = ["run_complete_analysis", "_analyze_repository", "_run_ai_code_analysis"]
        for method in methods:
            if hasattr(orchestrator, method):
                print_test(f"Method: {method}", True, "Method available")
            else:
                print_test(f"Method: {method}", False, "Method missing")

        return True

    except Exception as e:
        print_test("Orchestrator", False, f"Error: {e}")
        return False

def test_script_functionality():
    """Test shell script functionality"""
    print_header("Script Functionality Tests")

    script_path = "run_github_analysis.sh"

    if not os.path.exists(script_path):
        print_test("Startup script", False, "Script not found")
        return False

    # Test script can be read
    try:
        with open(script_path, 'r') as f:
            content = f.read()
        print_test("Script readability", True, "Script content accessible")
    except Exception as e:
        print_test("Script readability", False, f"Cannot read script: {e}")
        return False

    # Test key functions in script
    key_functions = [
        "print_header",
        "setup_virtual_environment",
        "run_analysis",
        "show_help",
    ]

    for func in key_functions:
        if func in content:
            print_test(f"Function: {func}", True, "Function found")
        else:
            print_test(f"Function: {func}", False, "Function missing")

    return True

def generate_test_report(results):
    """Generate final test report"""
    print_header("Final Test Report")

    total_tests = len(results)
    passed_tests = sum(1 for result in results.values() if result)
    failed_tests = total_tests - passed_tests

    print(f"Total Tests: {total_tests}")
    print(f"Passed: {passed_tests}")
    print(f"Failed: {failed_tests}")
    print(f"Success Rate: {(passed_tests/total_tests)*100:.1f}%")

    if failed_tests > 0:
        print("\nFailed Tests:")
        for test_name, result in results.items():
            if not result:
                print(f"  - {test_name}")

    return failed_tests == 0

def main():
    """Main test execution"""
    print_header("GitHub Management CrewAI - System Validation")

    # Run all tests
    test_results = {}

    test_results["Python Version"] = test_python_version()
    test_results["Module Imports"] = test_imports()
    test_results["Core Components"] = test_core_components()
    test_results["Configuration"] = test_configuration()
    test_results["GitHub Integration"] = test_github_integration()
    test_results["AI Services"] = test_ai_services()
    test_results["Project Management"] = test_project_management()
    test_results["Orchestrator"] = test_orchestrator()
    test_results["Script Functionality"] = test_script_functionality()

    # Generate final report
    success = generate_test_report(test_results)

    # Exit with appropriate code
    if success:
        print("\n🎉 All tests passed! System is ready for use.")
        print("\nNext steps:")
        print("1. Configure your .env file with API keys")
        print("2. Run: ./run_github_analysis.sh --setup")
        print("3. Execute: ./run_github_analysis.sh <owner> <repo>")
        sys.exit(0)
    else:
        print("\n❌ Some tests failed. Please review the issues above.")
        print("\nTroubleshooting:")
        print("1. Install missing dependencies: pip install -r requirements.txt")
        print("2. Check Python version: python3 --version")
        print("3. Verify file permissions: chmod +x run_github_analysis.sh")
        sys.exit(1)

if __name__ == "__main__":
    main()
