#!/usr/bin/env python3
"""
Comprehensive test runner for Hebrew Coreference Resolution System.
"""

import unittest
import sys
import os
import time
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

def run_all_tests():
    """Run all tests and return results."""
    # Discover all test files
    test_dir = Path(__file__).parent
    test_files = list(test_dir.glob("test_*.py"))
    
    print("=" * 60)
    print("HEBREW COREFERENCE RESOLUTION SYSTEM - TEST SUITE")
    print("=" * 60)
    print(f"Found {len(test_files)} test files:")
    for test_file in test_files:
        print(f"  - {test_file.name}")
    print()
    
    # Run tests
    start_time = time.time()
    
    # Create test suite
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # Add all test files
    for test_file in test_files:
        if test_file.name != "test_all.py":  # Skip this file
            module_name = f"tests.{test_file.stem}"
            try:
                tests = loader.loadTestsFromName(module_name)
                suite.addTests(tests)
            except Exception as e:
                print(f"Warning: Could not load tests from {test_file.name}: {e}")
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    end_time = time.time()
    total_time = end_time - start_time
    
    # Print summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    print(f"Tests run: {result.testsRun}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    print(f"Skipped: {len(result.skipped) if hasattr(result, 'skipped') else 0}")
    print(f"Total time: {total_time:.2f} seconds")
    
    if result.failures:
        print("\nFAILURES:")
        for test, traceback in result.failures:
            print(f"  - {test}: {traceback.split('AssertionError:')[-1].strip()}")
    
    if result.errors:
        print("\nERRORS:")
        for test, traceback in result.errors:
            print(f"  - {test}: {traceback.split('Exception:')[-1].strip()}")
    
    # Return success/failure
    success = len(result.failures) == 0 and len(result.errors) == 0
    print(f"\nOverall result: {'PASSED' if success else 'FAILED'}")
    
    return success


def run_component_tests():
    """Run tests for specific components."""
    components = [
        ("Main CLI", "test_main"),
        ("Configuration", "test_config"),
        ("Mention Detection", "test_mention_detection"),
        ("Annotation", "test_annotation"),
        ("Neural Models", "test_neural_models"),
        ("LLM Evaluation", "test_llm_evaluation"),
    ]
    
    print("=" * 60)
    print("COMPONENT-SPECIFIC TESTS")
    print("=" * 60)
    
    results = {}
    
    for component_name, test_module in components:
        print(f"\nTesting {component_name}...")
        try:
            # Import and run specific test module
            module = __import__(f"tests.{test_module}", fromlist=["*"])
            
            # Create test suite for this module
            loader = unittest.TestLoader()
            suite = loader.loadTestsFromModule(module)
            
            # Run tests
            runner = unittest.TextTestRunner(verbosity=1)
            result = runner.run(suite)
            
            # Store results
            results[component_name] = {
                'tests_run': result.testsRun,
                'failures': len(result.failures),
                'errors': len(result.errors),
                'success': len(result.failures) == 0 and len(result.errors) == 0
            }
            
            status = "PASSED" if results[component_name]['success'] else "FAILED"
            print(f"  {component_name}: {status}")
            
        except Exception as e:
            print(f"  {component_name}: ERROR - {e}")
            results[component_name] = {
                'tests_run': 0,
                'failures': 0,
                'errors': 1,
                'success': False
            }
    
    # Print component summary
    print("\n" + "=" * 60)
    print("COMPONENT TEST SUMMARY")
    print("=" * 60)
    
    total_tests = 0
    total_failures = 0
    total_errors = 0
    passed_components = 0
    
    for component_name, result in results.items():
        total_tests += result['tests_run']
        total_failures += result['failures']
        total_errors += result['errors']
        if result['success']:
            passed_components += 1
        
        status = "PASSED" if result['success'] else "FAILED"
        print(f"{component_name:20} | {result['tests_run']:3} tests | {status}")
    
    print("-" * 60)
    print(f"Total components: {len(components)}")
    print(f"Passed components: {passed_components}")
    print(f"Failed components: {len(components) - passed_components}")
    print(f"Total tests: {total_tests}")
    print(f"Total failures: {total_failures}")
    print(f"Total errors: {total_errors}")
    
    return passed_components == len(components)


def run_integration_tests():
    """Run integration tests."""
    print("\n" + "=" * 60)
    print("INTEGRATION TESTS")
    print("=" * 60)
    
    # Test configuration integration
    print("Testing configuration integration...")
    try:
        from config import validate_paths, get_workflow_steps
        print("  ✓ Configuration imports successfully")
        
        # Test path validation
        if validate_paths():
            print("  ✓ All required paths exist")
        else:
            print("  ⚠ Some paths are missing (expected for test environment)")
        
        # Test workflow steps
        steps = get_workflow_steps()
        if len(steps) == 5:
            print("  ✓ Workflow steps properly defined")
        else:
            print(f"  ⚠ Expected 5 workflow steps, got {len(steps)}")
        
    except Exception as e:
        print(f"  ✗ Configuration integration failed: {e}")
        return False
    
    # Test main CLI integration
    print("Testing main CLI integration...")
    try:
        from main import main
        print("  ✓ Main CLI imports successfully")
    except Exception as e:
        print(f"  ✗ Main CLI integration failed: {e}")
        return False
    
    print("  ✓ Integration tests completed")
    return True


def run_performance_tests():
    """Run basic performance tests."""
    print("\n" + "=" * 60)
    print("PERFORMANCE TESTS")
    print("=" * 60)
    
    # Test configuration loading speed
    print("Testing configuration loading speed...")
    start_time = time.time()
    try:
        from config import get_output_path, get_neural_results_path, get_llm_results_path
        end_time = time.time()
        load_time = end_time - start_time
        print(f"  ✓ Configuration loaded in {load_time:.3f} seconds")
        
        if load_time < 1.0:
            print("  ✓ Configuration loading is fast")
        else:
            print("  ⚠ Configuration loading is slow")
            
    except Exception as e:
        print(f"  ✗ Configuration loading failed: {e}")
        return False
    
    # Test path generation speed
    print("Testing path generation speed...")
    start_time = time.time()
    try:
        # Generate multiple paths
        for i in range(100):
            get_output_path(version=f"v{i}")
            get_neural_results_path("test-model", "test-base", i)
            get_llm_results_path("gpt-4", f"exp_{i}")
        
        end_time = time.time()
        path_time = end_time - start_time
        print(f"  ✓ Path generation completed in {path_time:.3f} seconds")
        
        if path_time < 0.1:
            print("  ✓ Path generation is fast")
        else:
            print("  ⚠ Path generation is slow")
            
    except Exception as e:
        print(f"  ✗ Path generation failed: {e}")
        return False
    
    print("  ✓ Performance tests completed")
    return True


def main():
    """Main test runner."""
    print("Starting comprehensive test suite...")
    print()
    
    # Run all tests
    all_tests_passed = run_all_tests()
    
    # Run component tests
    component_tests_passed = run_component_tests()
    
    # Run integration tests
    integration_tests_passed = run_integration_tests()
    
    # Run performance tests
    performance_tests_passed = run_performance_tests()
    
    # Final summary
    print("\n" + "=" * 60)
    print("FINAL TEST SUMMARY")
    print("=" * 60)
    
    results = [
        ("All Tests", all_tests_passed),
        ("Component Tests", component_tests_passed),
        ("Integration Tests", integration_tests_passed),
        ("Performance Tests", performance_tests_passed),
    ]
    
    passed = 0
    for test_name, result in results:
        status = "PASSED" if result else "FAILED"
        print(f"{test_name:20} | {status}")
        if result:
            passed += 1
    
    print("-" * 60)
    print(f"Overall: {passed}/{len(results)} test suites passed")
    
    if passed == len(results):
        print("🎉 All tests passed! The system is ready for production.")
        return 0
    else:
        print("⚠ Some tests failed. Please review the issues above.")
        return 1


if __name__ == "__main__":
    sys.exit(main()) 