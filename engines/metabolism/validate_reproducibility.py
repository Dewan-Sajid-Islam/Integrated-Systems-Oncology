# validate_reproducibility.py
"""
Validation of deterministic execution.

Tests:
- Same random seed produces identical histories.
- Different random seed produces different histories.
"""

import sys
import numpy as np
from engine import SimulationConfig, MetabolismEngine


def compare_results(res1, res2, label):
    """Compare two SimulationResults objects; return True if all relevant fields match."""
    match = True
    # Compare scalar metric histories (lists)
    for key in ['mean_atp', 'mean_oxygen', 'mean_glucose', 'mean_lactate',
                'mean_ph', 'mean_ros', 'hypoxia_index', 'necrosis_fraction',
                'metabolic_stress']:
        val1 = getattr(res1, key)
        val2 = getattr(res2, key)
        if val1 != val2:
            print(f"  {label}: {key} differs")
            match = False
    # Compare spatial histories (lists of arrays)
    for key in ['oxygen_hist', 'glucose_hist', 'lactate_hist', 'atp_hist',
                'ph_hist', 'ros_hist', 'hypoxia_hist', 'stress_hist',
                'necrosis_hist', 'phenotype_hist']:
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
    return match


def test_reproducibility():
    cfg = SimulationConfig(
        random_seed=42,
        time_steps=10,
        dt=0.1,
        num_regions=8,
        vascular_density=0.2,
        strict_validation=False,
        development_mode=False,
    )

    # Same seed twice
    eng1 = MetabolismEngine(cfg)
    res1 = eng1.run()
    eng2 = MetabolismEngine(cfg)
    res2 = eng2.run()
    same_seed_match = compare_results(res1, res2, "Same seed")

    # Different seed
    cfg2 = SimulationConfig(**cfg.__dict__)
    cfg2.random_seed = 123
    eng3 = MetabolismEngine(cfg2)
    res3 = eng3.run()
    # Check that at least one history differs.
    # We'll compare mean_atp histories; they should differ.
    diff_seed_diff = (res1.mean_atp != res3.mean_atp)

    passed = same_seed_match and diff_seed_diff

    print("validate_reproducibility")
    print(f"  Same seed: identical? {same_seed_match}")
    print(f"  Different seed: histories differ? {diff_seed_diff}")
    print(f"  RESULT: {'PASS' if passed else 'FAIL'}")
    return passed


if __name__ == "__main__":
    sys.exit(0 if test_reproducibility() else 1)