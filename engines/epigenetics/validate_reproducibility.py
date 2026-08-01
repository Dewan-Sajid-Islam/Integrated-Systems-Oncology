# validate_reproducibility.py
"""
Validation of deterministic reproducibility.

Tests:
- Same random seed produces identical histories, summary metrics, and distributions.
- If the simulation uses randomness (e.g., expression_noise > 0), different seeds must
  produce different expression histories. If no randomness is present, we print a message
  and only verify that the same seed yields identical results.
"""

import sys
import time
import numpy as np
from engine import SimulationConfig, EpigeneticsEngine


def compare_results(res1, res2, label):
    """Compare two SimulationResults objects; return True if all relevant fields match."""
    match = True
    # Compare scalar metric histories (lists)
    for key in ['mean_methylation', 'mean_acetylation', 'mean_accessibility',
                'mean_expression', 'mean_instability', 'mean_plasticity',
                'mean_stemness', 'mean_differentiation', 'mean_stress',
                'mean_epigenetic_age']:
        val1 = getattr(res1, key)
        val2 = getattr(res2, key)
        if val1 != val2:
            print(f"  {label}: {key} differs")
            match = False
    # Compare spatial histories (lists of arrays)
    for key in ['methylation_hist', 'acetylation_hist', 'accessibility_hist',
                'expression_hist', 'instability_hist', 'plasticity_hist',
                'stemness_hist', 'differentiation_hist', 'stress_hist',
                'epigenetic_age_hist']:
        hist1 = getattr(res1, key)
        hist2 = getattr(res2, key)
        if len(hist1) != len(hist2):
            print(f"  {label}: {key} length differs")
            match = False
            continue
        for arr1, arr2 in zip(hist1, hist2):
            if not np.array_equal(arr1, arr2):
                print(f"  {label}: {key} array differs")
                match = False
                break
    # Compare distributions
    if res1.differentiation_dist != res2.differentiation_dist:
        print(f"  {label}: differentiation_dist differs")
        match = False
    if res1.chromatin_dist != res2.chromatin_dist:
        print(f"  {label}: chromatin_dist differs")
        match = False
    if res1.stemness_dist != res2.stemness_dist:
        print(f"  {label}: stemness_dist differs")
        match = False
    return match


def test_reproducibility():
    # Use a configuration with expression_noise > 0 to ensure randomness.
    cfg = SimulationConfig(
        random_seed=42,
        time_steps=8,
        dt=0.1,
        num_regions=5,
        development_mode=False,
        strict_validation=False,
        expression_noise=0.02,  # stochastic
    )
    start = time.perf_counter()

    # Same seed twice
    eng1 = EpigeneticsEngine(cfg)
    res1 = eng1.run()
    eng2 = EpigeneticsEngine(cfg)
    res2 = eng2.run()
    same_seed_match = compare_results(res1, res2, "Same seed")

    # Check if randomness is present in the configuration
    stochastic_params = [
        cfg.expression_noise,
        # future stochastic parameters could be added here
    ]
    has_randomness = any(p > 0.0 for p in stochastic_params)

    diff_seed_diff = True
    if has_randomness:
        # Different seed should yield different expression histories
        cfg2 = SimulationConfig(**cfg.__dict__)
        cfg2.random_seed = 123
        eng3 = EpigeneticsEngine(cfg2)
        res3 = eng3.run()
        # Compare mean_expression (stochastic) rather than deterministic variables
        diff_seed_diff = (res1.mean_expression != res3.mean_expression)
        if not diff_seed_diff:
            print("  Different seed produced identical mean_expression histories")
    else:
        # No randomness; we only require same seed match
        print("  Engine deterministic by design (no stochastic parameters).")
        diff_seed_diff = True  # no requirement for divergence

    elapsed = time.perf_counter() - start

    passed = same_seed_match and diff_seed_diff

    print("validate_reproducibility")
    print(f"  Same seed: identical? {same_seed_match}")
    if has_randomness:
        print(f"  Different seed: expression histories differ? {diff_seed_diff}")
    else:
        print("  Different seed check skipped (deterministic mode).")
    print(f"  Execution time: {elapsed:.3f} seconds")
    print(f"  RESULT: {'PASS' if passed else 'FAIL'}")
    return passed


if __name__ == "__main__":
    sys.exit(0 if test_reproducibility() else 1)