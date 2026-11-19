#!/usr/bin/env python
"""
API Validation Script for Atmospheric Blocking Module

This script validates:
1. Module structure and imports
2. Function signatures
3. Documentation completeness
4. API consistency

Run without dependencies to check structure.
"""

import ast
from pathlib import Path


def check_module_structure():
    """Validate module file structure."""
    print("=" * 70)
    print("CHECKING MODULE STRUCTURE")
    print("=" * 70)

    base = Path("pcmdi_metrics/blocking")

    required_files = [
        "__init__.py",
        "README.md",
        "lib/__init__.py",
        "lib/blocking_detection.py",
        "lib/blocking_metrics.py",
        "lib/blocking_utils.py",
        "blocking_driver.py",
        "param/blocking_cmip6_example.py",
        "data/README_model.md",
    ]

    missing = []
    for file in required_files:
        path = base / file
        if path.exists():
            print(f"✓ {file}")
        else:
            print(f"✗ {file} - MISSING")
            missing.append(file)

    if missing:
        print(f"\n❌ Missing {len(missing)} required files")
        return False
    else:
        print(f"\n✅ All {len(required_files)} required files present")
        return True


def check_public_api():
    """Validate public API exports."""
    print("\n" + "=" * 70)
    print("CHECKING PUBLIC API")
    print("=" * 70)

    init_file = Path("pcmdi_metrics/blocking/__init__.py")
    with open(init_file) as f:
        content = f.read()

    # Check for __all__ definition
    if "__all__" in content:
        print("✓ __all__ defined")
    else:
        print("✗ __all__ not defined")
        return False

    # Expected public functions
    expected_api = [
        "detect_blocking",
        "compute_blocking_metrics",
        "metrics_to_json",
        "metrics_to_csv",
        "spatial_means_to_npy",
    ]

    for func in expected_api:
        if f'"{func}"' in content or f"'{func}'" in content:
            print(f"✓ {func} exported")
        else:
            print(f"✗ {func} not exported")
            return False

    print(f"\n✅ All {len(expected_api)} expected functions exported")
    return True


def check_function_signatures():
    """Parse and validate function signatures."""
    print("\n" + "=" * 70)
    print("CHECKING FUNCTION SIGNATURES")
    print("=" * 70)

    files_to_check = {
        "pcmdi_metrics/blocking/lib/blocking_detection.py": ["detect_blocking"],
        "pcmdi_metrics/blocking/lib/blocking_metrics.py": [
            "compute_blocking_metrics",
            "metrics_to_json",
        ],
    }

    all_valid = True

    for filepath, functions in files_to_check.items():
        with open(filepath) as f:
            tree = ast.parse(f.read())

        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef) and node.name in functions:
                # Check for type hints
                has_return_type = node.returns is not None
                args_with_types = sum(
                    1 for arg in node.args.args if arg.annotation is not None
                )
                total_args = len(node.args.args)

                print(f"\n{node.name}():")
                print(f"  Args: {total_args}")
                print(f"  Type hints: {args_with_types}/{total_args} args")
                print(f"  Return type: {'✓' if has_return_type else '✗'}")

                # Check for docstring
                docstring = ast.get_docstring(node)
                if docstring:
                    print(f"  Docstring: ✓ ({len(docstring)} chars)")

                    # Check for key sections
                    sections = {
                        "Parameters": "Parameters" in docstring,
                        "Returns": "Returns" in docstring,
                        "Examples": "Examples" in docstring,
                    }
                    for section, present in sections.items():
                        print(f"    - {section}: {'✓' if present else '✗'}")
                else:
                    print("  Docstring: ✗ MISSING")
                    all_valid = False

    if all_valid:
        print("\n✅ All main functions have proper signatures and docstrings")
    else:
        print("\n❌ Some functions missing docstrings")

    return all_valid


def check_dependencies():
    """Check optional dependency handling."""
    print("\n" + "=" * 70)
    print("CHECKING TENSORFLOW DEPENDENCY HANDLING")
    print("=" * 70)

    detection_file = Path("pcmdi_metrics/blocking/lib/blocking_detection.py")
    with open(detection_file) as f:
        content = f.read()

    checks = {
        "TensorFlow import guarded": "try:" in content
        and "import tensorflow" in content,
        "ImportError caught": "except ImportError" in content,
        "Helpful error message": '"TensorFlow is required' in content,
    }

    all_valid = True
    for check, passed in checks.items():
        if passed:
            print(f"✓ {check}")
        else:
            print(f"✗ {check}")
            all_valid = False

    if all_valid:
        print("\n✅ TensorFlow dependency properly handled")
    else:
        print("\n❌ TensorFlow dependency handling incomplete")

    return all_valid


def check_driver_script():
    """Validate driver script structure."""
    print("\n" + "=" * 70)
    print("CHECKING DRIVER SCRIPT")
    print("=" * 70)

    driver_file = Path("pcmdi_metrics/blocking/blocking_driver.py")
    with open(driver_file) as f:
        content = f.read()

    checks = {
        "main() function": "def main(" in content,
        "Uses detect_blocking API": "detect_blocking(" in content,
        "Uses compute_blocking_metrics API": "compute_blocking_metrics(" in content,
        "Parallel processing": "multiprocessing" in content,
        "Logging": "import logging" in content,
        "__main__ guard": 'if __name__ == "__main__"' in content,
    }

    all_valid = True
    for check, passed in checks.items():
        if passed:
            print(f"✓ {check}")
        else:
            print(f"✗ {check}")
            all_valid = False

    if all_valid:
        print("\n✅ Driver script properly structured")
    else:
        print("\n❌ Driver script incomplete")

    return all_valid


def check_documentation():
    """Validate documentation files."""
    print("\n" + "=" * 70)
    print("CHECKING DOCUMENTATION")
    print("=" * 70)

    docs = {
        "Module README": Path("pcmdi_metrics/blocking/README.md"),
        "Model README": Path("pcmdi_metrics/blocking/data/README_model.md"),
    }

    all_valid = True
    for name, path in docs.items():
        if path.exists():
            size = path.stat().st_size
            with open(path) as f:
                content = f.read()
                lines = len(content.split("\n"))
            print(f"✓ {name}: {lines} lines, {size} bytes")

            # Check for key sections
            if name == "Module README":
                required_sections = [
                    "Installation",
                    "Quick Start",
                    "Usage",
                    "Examples",
                ]
                for section in required_sections:
                    if section in content:
                        print(f"  ✓ Has {section!r} section")
                    else:
                        print(f"  ✗ Missing '{section}' section")
                        all_valid = False
        else:
            print(f"✗ {name}: MISSING")
            all_valid = False

    if all_valid:
        print("\n✅ Documentation complete")
    else:
        print("\n❌ Documentation incomplete")

    return all_valid


def check_code_quality():
    """Check for common code quality issues."""
    print("\n" + "=" * 70)
    print("CHECKING CODE QUALITY")
    print("=" * 70)

    python_files = list(Path("pcmdi_metrics/blocking").rglob("*.py"))

    issues = []

    for filepath in python_files:
        if "__pycache__" in str(filepath):
            continue

        with open(filepath) as f:
            content = f.read()

        # Check for common issues
        if "import *" in content:
            issues.append(f"{filepath}: Uses 'import *'")

        # Check for TODO/FIXME
        for i, line in enumerate(content.split("\n"), 1):
            if "TODO" in line or "FIXME" in line:
                issues.append(f"{filepath}:{i}: Contains TODO/FIXME")

    if issues:
        print(f"❌ Found {len(issues)} code quality issues:")
        for issue in issues[:10]:  # Show first 10
            print(f"  - {issue}")
        if len(issues) > 10:
            print(f"  ... and {len(issues) - 10} more")
        return False
    else:
        print(f"✅ No code quality issues found in {len(python_files)} Python files")
        return True


def main():
    """Run all validation checks."""
    print("\n" + "=" * 70)
    print("ATMOSPHERIC BLOCKING MODULE - API VALIDATION")
    print("=" * 70)

    checks = [
        ("Module Structure", check_module_structure),
        ("Public API", check_public_api),
        ("Function Signatures", check_function_signatures),
        ("Dependencies", check_dependencies),
        ("Driver Script", check_driver_script),
        ("Documentation", check_documentation),
        ("Code Quality", check_code_quality),
    ]

    results = {}
    for name, check_func in checks:
        try:
            results[name] = check_func()
        except Exception as e:
            print(f"\n❌ Error checking {name}: {e}")
            results[name] = False

    # Summary
    print("\n" + "=" * 70)
    print("VALIDATION SUMMARY")
    print("=" * 70)

    for name, passed in results.items():
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status}: {name}")

    total = len(results)
    passed = sum(results.values())

    print(f"\nTotal: {passed}/{total} checks passed")

    if passed == total:
        print("\n🎉 ALL VALIDATION CHECKS PASSED!")
        return 0
    else:
        print(f"\n⚠️  {total - passed} validation check(s) failed")
        return 1


if __name__ == "__main__":
    exit(main())
