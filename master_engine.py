#!/usr/bin/env python3
"""
Integrated Systems Oncology — Master Engine

This script orchestrates the execution of the four independent engines:
Tumor Evolution, Metabolism, Epigenetics, and Synergy.

It runs each engine as a separate subprocess, captures output and timing,
and produces a professional summary. It does not import or modify any engine
code directly; each engine is executed as a standalone Python script.

Usage:
    python master_engine.py

Returns exit code 0 if all engines pass, otherwise 1.
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


def locate_engines() -> dict[str, Path]:
    """
    Locate the engine directories relative to this script's location.

    Returns a dictionary mapping engine display name to its path.
    Raises FileNotFoundError if any engine directory is missing.
    """
    script_dir = Path(__file__).parent.resolve()
    engines_dir = script_dir / "engines"
    if not engines_dir.is_dir():
        raise FileNotFoundError(f"Engines directory not found: {engines_dir}")

    engine_paths = {}
    for display_name, folder_name in ENGINES:
        engine_path = engines_dir / folder_name
        if not engine_path.is_dir():
            raise FileNotFoundError(f"Engine directory not found: {engine_path}")
        engine_py = engine_path / "engine.py"
        if not engine_py.is_file():
            raise FileNotFoundError(f"engine.py not found in {engine_path}")
        engine_paths[display_name] = engine_path
    return engine_paths


def run_engine(display_name: str, engine_path: Path) -> tuple[bool, str, float]:
    """
    Run a single engine as a subprocess.

    Returns a tuple (success, output, runtime_in_seconds).
    """
    engine_py = engine_path / "engine.py"
    start_time = time.perf_counter()
    try:
        result = subprocess.run(
            [sys.executable, str(engine_py)],
            cwd=str(engine_path),
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=120,
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
    print("Master Engine")
    print(f"Version {VERSION}")
    print("=" * 60)


def print_summary(results: list[tuple[str, bool, float, str]]) -> None:
    """
    Print a formatted summary table and final overall result.

    results: list of (display_name, success, runtime, output)
    """
    print("\n" + "=" * 60)
    print("Master Summary")
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
    print(f"Overall: {'PASS' if all_passed else 'FAIL'}")
    print(f"Total runtime: {total_runtime:.2f} seconds")
    print("=" * 60)


def main() -> int:
    """Main entry point."""
    print_banner()

    try:
        engine_paths = locate_engines()
    except FileNotFoundError as e:
        print(f"ERROR: {e}")
        return 1

    results = []

    for display_name, folder_name in ENGINES:
        engine_path = engine_paths.get(display_name)
        if engine_path is None:
            print(f"ERROR: Engine '{display_name}' not found.")
            results.append((display_name, False, 0.0, "Engine not found"))
            continue

        print(f"Running {display_name} ...", end="", flush=True)
        success, output, runtime = run_engine(display_name, engine_path)
        status = "PASS" if success else "FAIL"
        print(f" {status} ({runtime:.2f} s)")
        results.append((display_name, success, runtime, output))

    print_summary(results)
    return 0 if all(success for _, success, _, _ in results) else 1


if __name__ == "__main__":
    sys.exit(main())