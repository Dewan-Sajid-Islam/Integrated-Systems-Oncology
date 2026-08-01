#!/usr/bin/env python3
"""
Integrated Systems Oncology — Project Validation Suite

This script runs the validation suite for each of the four engines
(Tumor Evolution, Metabolism, Epigenetics, Synergy) by executing their
validate_all.py scripts as subprocesses. It collects results and
produces a summary report.

Usage:
    python validate_project.py

Returns exit code 0 if all validations pass, otherwise 1.
"""

import subprocess
import sys
import time
from pathlib import Path


VERSION = "1.0.0"
ENGINES = [
    ("Tumor Evolution", "tumor_evolution"),
    ("Metabolism", "metabolism"),
    ("Epigenetics", "epigenetics"),
    ("Synergy", "synergy"),
]


def locate_validators() -> dict[str, Path]:
    """
    Locate the validate_all.py scripts for each engine.

    Returns a dictionary mapping display name to the path of the validator script.
    Raises FileNotFoundError if any script is missing.
    """
    script_dir = Path(__file__).parent.resolve()
    engines_dir = script_dir / "engines"
    if not engines_dir.is_dir():
        raise FileNotFoundError(f"Engines directory not found: {engines_dir}")

    validators = {}
    for display_name, folder_name in ENGINES:
        engine_path = engines_dir / folder_name
        validator = engine_path / "validate_all.py"
        if not validator.is_file():
            raise FileNotFoundError(f"validate_all.py not found: {validator}")
        validators[display_name] = validator
    return validators


def run_validator(display_name: str, validator_path: Path) -> tuple[bool, str, float]:
    """
    Run a single validation suite as a subprocess.

    Returns a tuple (success, output, runtime_in_seconds).
    """
    start_time = time.perf_counter()
    try:
        result = subprocess.run(
            [sys.executable, str(validator_path)],
            cwd=str(validator_path.parent),
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=180,
        )
        runtime = time.perf_counter() - start_time
        output = result.stdout + result.stderr
        success = (result.returncode == 0)
        return success, output, runtime
    except subprocess.TimeoutExpired:
        runtime = time.perf_counter() - start_time
        return False, "TIMEOUT", runtime
    except Exception as e:
        runtime = time.perf_counter() - start_time
        return False, f"ERROR: {e}", runtime


def print_banner() -> None:
    """Print the opening banner."""
    print("=" * 60)
    print("Integrated Systems Oncology")
    print("Project Validation Suite")
    print(f"Version {VERSION}")
    print("=" * 60)


def print_summary(results: list[tuple[str, bool, float, str]]) -> None:
    """
    Print a formatted summary table and final overall result.

    results: list of (display_name, success, runtime, output)
    """
    print("\n" + "=" * 60)
    print("Project Validation Summary")
    print("=" * 60)

    max_name_len = max(len(name) for name, _, _, _ in results)
    for display_name, success, runtime, output in results:
        status = "PASS" if success else "FAIL"
        print(f"{display_name:>{max_name_len}} ..... {status} ({runtime:.2f} s)")
        if not success:
            # Print a snippet of stderr for debugging
            lines = output.splitlines()
            # Show last few lines (or relevant error lines)
            error_lines = [line for line in lines if "Error" in line or "Traceback" in line or "Exception" in line]
            if error_lines:
                for line in error_lines[-3:]:
                    print(f"  {line}")
            else:
                for line in lines[-3:]:
                    print(f"  {line}")

    print("=" * 60)
    total_runtime = sum(runtime for _, _, runtime, _ in results)
    all_passed = all(success for _, success, _, _ in results)
    print(f"Overall Project Validation: {'PASS' if all_passed else 'FAIL'}")
    print(f"Total Runtime: {total_runtime:.2f} seconds")
    print("=" * 60)


def main() -> int:
    """Main entry point."""
    print_banner()

    try:
        validators = locate_validators()
    except FileNotFoundError as e:
        print(f"ERROR: {e}")
        return 1

    results = []

    for display_name, folder_name in ENGINES:
        validator_path = validators.get(display_name)
        if validator_path is None:
            print(f"ERROR: Validator for '{display_name}' not found.")
            results.append((display_name, False, 0.0, "Validator not found"))
            continue

        print(f"Running {display_name} Validation ...", end="", flush=True)
        success, output, runtime = run_validator(display_name, validator_path)
        status = "PASS" if success else "FAIL"
        print(f" {status} ({runtime:.2f} s)")
        results.append((display_name, success, runtime, output))

    print_summary(results)
    return 0 if all(success for _, success, _, _ in results) else 1


if __name__ == "__main__":
    sys.exit(main())