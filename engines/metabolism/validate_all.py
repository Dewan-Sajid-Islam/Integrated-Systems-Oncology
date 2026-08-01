# validate_all.py
"""
Run all validation scripts and produce a professional summary.
"""

import subprocess
import sys
import time
import os


def sanitize_output(text):
    """
    Replace Unicode characters that may cause encoding errors on Windows consoles.
    """
    # Replace check mark and cross mark with ASCII equivalents
    text = text.replace('✓', 'PASS')
    text = text.replace('✗', 'FAIL')
    # Also replace any other non-ASCII with '?' if needed
    # But we can just encode and decode with replace to be safe
    try:
        # Attempt to encode with the console encoding, replacing errors
        encoding = sys.stdout.encoding or 'utf-8'
        return text.encode(encoding, errors='replace').decode(encoding)
    except Exception:
        # Fallback: remove all non-ASCII
        return ''.join(c if ord(c) < 128 else '?' for c in text)


def run_script(script_name):
    """Execute a validation script and return (passed, output, runtime)."""
    start = time.time()
    try:
        # Use utf-8 encoding for subprocess to capture correctly
        result = subprocess.run(
            [sys.executable, script_name],
            capture_output=True,
            text=True,
            encoding='utf-8',
            timeout=60,
            check=False
        )
        runtime = time.time() - start
        # Combine stdout and stderr
        raw_output = result.stdout + result.stderr
        # Sanitize to avoid UnicodeEncodeError on Windows
        output = sanitize_output(raw_output)

        # Determine pass/fail by looking for "RESULT: PASS" or "RESULT: FAIL"
        if "RESULT: PASS" in output:
            passed = True
        elif "RESULT: FAIL" in output:
            passed = False
        else:
            # Fallback: exit code 0 => pass
            passed = (result.returncode == 0)
        return passed, output, runtime
    except Exception as e:
        return False, f"Error: {e}", 0.0


def main():
    scripts = [
        "validate_diffusion.py",
        "validate_metabolism.py",
        "validate_phenotypes.py",
        "validate_reproducibility.py"
    ]

    results = {}
    outputs = {}
    runtimes = {}
    all_passed = True

    print("=" * 60)
    print("Integrated Systems Oncology")
    print("Metabolism Validation Suite")
    print("=" * 60)

    for script in scripts:
        if not os.path.isfile(script):
            print(f"ERROR: {script} not found.")
            results[script] = False
            outputs[script] = "File not found"
            runtimes[script] = 0.0
            all_passed = False
            continue

        passed, output, runtime = run_script(script)
        results[script] = passed
        outputs[script] = output
        runtimes[script] = runtime
        if not passed:
            all_passed = False

        # Print status line
        status = "PASS" if passed else "FAIL"
        print(f"{script:30} {status}  ({runtime:.2f} s)")

        # If failed, print the last few lines of output to help debug
        if not passed:
            print("-" * 40)
            lines = output.splitlines()
            # Show only lines containing "FAIL", "Error", or "Traceback"
            relevant = [line for line in lines if any(k in line for k in ("FAIL", "Error", "Traceback", "Exception"))]
            if relevant:
                for line in relevant[-5:]:
                    print(line)
            else:
                # Fallback: print last 5 lines
                for line in lines[-5:]:
                    print(line)
            print("-" * 40)

    print("=" * 60)
    passed_count = sum(results.values())
    total = len(results)
    total_runtime = sum(runtimes.values())
    print(f"Passed: {passed_count} / {total}")
    print(f"Total runtime: {total_runtime:.2f} s")
    print(f"OVERALL RESULT: {'PASS' if all_passed else 'FAIL'}")
    print("=" * 60)

    sys.exit(0 if all_passed else 1)


if __name__ == "__main__":
    main()