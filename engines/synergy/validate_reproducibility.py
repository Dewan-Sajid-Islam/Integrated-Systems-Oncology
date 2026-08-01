# validate_reproducibility.py
"""
Validation of deterministic reproducibility of the Synergy Engine.

Tests:
1. Same seed: identical histories for all recorded metrics.
2. Same seed: identical final state arrays.
3. Same seed: identical summary statistics.
4. Same seed: identical combined fitness history.
5. Same seed: identical adaptive capacity history.
6. Same seed: identical therapy resistance history.
7. Same seed: identical mutation pressure history.
8. Same seed: identical system stability history.
9. Different seeds: different histories (when stochasticity exists).
10. Different seeds: different final spatial distributions.
11. Array shapes remain identical across runs.
12. No NaN/Inf in any history.
13. Execution completes without errors.
"""

import sys
import numpy as np
from engine import SimulationConfig, SynergyEngine


def run_simulation(seed=42, **kwargs):
    cfg = SimulationConfig(random_seed=seed, **kwargs)
    eng = SynergyEngine(cfg)
    res = eng.run()
    return eng, res


def compare_results(res1, res2, label):
    """Compare two SimulationResults objects; return True if all relevant fields match."""
    match = True
    # Compare scalar metric histories (lists)
    for key in ['mean_combined_fitness', 'mean_mutation_pressure',
                'mean_therapy_resistance', 'mean_adaptive_capacity',
                'mean_resilience', 'mean_stability', 'mean_stemness',
                'mean_plasticity', 'mean_metabolic_stress',
                'mean_oxidative_stress', 'mean_hypoxia']:
        val1 = getattr(res1, key)
        val2 = getattr(res2, key)
        if val1 != val2:
            print(f"  {label}: {key} differs")
            match = False
    # Compare spatial histories (lists of arrays)
    hist_keys = [
        'tumor_fitness_hist', 'metabolic_fitness_hist', 'epigenetic_fitness_hist',
        'combined_fitness_hist', 'stemness_hist', 'plasticity_hist',
        'mutation_pressure_hist', 'selection_pressure_hist', 'metabolic_stress_hist',
        'oxidative_stress_hist', 'hypoxia_hist', 'chromatin_accessibility_hist',
        'gene_expression_hist', 'adaptive_capacity_hist', 'therapy_resistance_hist',
        'cellular_resilience_hist', 'system_stability_hist'
    ]
    for key in hist_keys:
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
    # Compare summary statistics
    summary_keys = [
        'final_combined_fitness', 'final_mutation_pressure', 'final_therapy_resistance',
        'final_adaptive_capacity', 'final_resilience', 'final_stability',
        'final_stemness', 'final_plasticity', 'final_metabolic_stress',
        'final_oxidative_stress', 'final_hypoxia', 'avg_combined_fitness'
    ]
    for key in summary_keys:
        if getattr(res1, key) != getattr(res2, key):
            print(f"  {label}: summary {key} differs")
            match = False
    return match


def test_reproducibility():
    base_cfg = {
        "time_steps": 20,
        "dt": 0.1,
        "num_regions": 5,
        "development_mode": False,
        "strict_validation": False,
    }

    # ------------------------------------------------------------------
    # Run two simulations with the same seed
    # ------------------------------------------------------------------
    eng1, res1 = run_simulation(seed=42, **base_cfg)
    eng2, res2 = run_simulation(seed=42, **base_cfg)

    # Test 1: Histories identical
    same_seed_hist = compare_results(res1, res2, "Same seed")
    print("Same seed: identical histories: " + ("PASS" if same_seed_hist else "FAIL"))

    # Test 2: Final state arrays identical
    state_vars = [
        "tumor_fitness", "metabolic_fitness", "epigenetic_fitness",
        "combined_fitness", "stemness", "plasticity", "mutation_pressure",
        "selection_pressure", "metabolic_stress", "oxidative_stress",
        "hypoxia", "chromatin_accessibility", "gene_expression",
        "adaptive_capacity", "therapy_resistance", "cellular_resilience",
        "system_stability"
    ]
    final_state_ok = True
    for var in state_vars:
        arr1 = getattr(eng1, var)
        arr2 = getattr(eng2, var)
        if not np.array_equal(arr1, arr2):
            final_state_ok = False
            print(f"  Same seed: {var} final arrays differ")
            break
    print("Same seed: identical final state arrays: " + ("PASS" if final_state_ok else "FAIL"))

    # Test 3: Summary statistics identical (already checked in compare_results, but we'll explicitly test)
    summary_ok = True
    summary_keys = [
        'final_combined_fitness', 'final_mutation_pressure', 'final_therapy_resistance',
        'final_adaptive_capacity', 'final_resilience', 'final_stability',
        'final_stemness', 'final_plasticity', 'final_metabolic_stress',
        'final_oxidative_stress', 'final_hypoxia', 'avg_combined_fitness'
    ]
    for key in summary_keys:
        if getattr(res1, key) != getattr(res2, key):
            summary_ok = False
            print(f"  Same seed: summary {key} differs")
            break
    print("Same seed: identical summary statistics: " + ("PASS" if summary_ok else "FAIL"))

    # Tests 4-8: Individual histories (already covered by test 1, but we explicitly check)
    hist_keys = {
        'combined_fitness_hist': 'combined fitness',
        'adaptive_capacity_hist': 'adaptive capacity',
        'therapy_resistance_hist': 'therapy resistance',
        'mutation_pressure_hist': 'mutation pressure',
        'system_stability_hist': 'system stability'
    }
    individual_ok = True
    for hist_key, label in hist_keys.items():
        h1 = getattr(res1, hist_key)
        h2 = getattr(res2, hist_key)
        if not all(np.array_equal(a, b) for a, b in zip(h1, h2)):
            individual_ok = False
            print(f"  Same seed: {label} history differs")
            break
    # We can print a single line for all
    print("Same seed: individual metric histories identical: " + ("PASS" if individual_ok else "FAIL"))

    # Test 9: Different seeds produce different histories (since heterogeneity differs)
    eng3, res3 = run_simulation(seed=123, **base_cfg)
    # Compare mean_combined_fitness lists; they should differ
    diff_hist = (res1.mean_combined_fitness != res3.mean_combined_fitness)
    print("Different seeds: histories differ: " + ("PASS" if diff_hist else "FAIL"))

    # Test 10: Different seeds produce different final spatial distributions
    # Compare final combined fitness arrays
    diff_spatial = not np.array_equal(eng1.combined_fitness, eng3.combined_fitness)
    print("Different seeds: final spatial distributions differ: " + ("PASS" if diff_spatial else "FAIL"))

    # Test 11: Array shapes identical across runs (check first run shapes)
    shape_ok = True
    n_regions = base_cfg["num_regions"]
    for var in state_vars:
        arr = getattr(eng1, var)
        if arr.shape != (n_regions,):
            shape_ok = False
            print(f"  {var} shape {arr.shape} != ({n_regions},)")
            break
    print("Array shapes identical: " + ("PASS" if shape_ok else "FAIL"))

    # Test 12: No NaN/Inf in histories
    nan_ok = True
    for hist_key in [
        'tumor_fitness_hist', 'metabolic_fitness_hist', 'epigenetic_fitness_hist',
        'combined_fitness_hist', 'stemness_hist', 'plasticity_hist',
        'mutation_pressure_hist', 'selection_pressure_hist', 'metabolic_stress_hist',
        'oxidative_stress_hist', 'hypoxia_hist', 'chromatin_accessibility_hist',
        'gene_expression_hist', 'adaptive_capacity_hist', 'therapy_resistance_hist',
        'cellular_resilience_hist', 'system_stability_hist'
    ]:
        hist = getattr(res1, hist_key)
        for arr in hist:
            if not np.all(np.isfinite(arr)):
                nan_ok = False
                print(f"  {hist_key} contains non-finite values")
                break
        if not nan_ok:
            break
    print("No NaN/Inf in histories: " + ("PASS" if nan_ok else "FAIL"))

    # Test 13: Execution completes (implicitly, but we check that no exception occurred)
    # We'll just assume it's okay since we got results.
    exec_ok = True
    print("Execution completes successfully: " + ("PASS" if exec_ok else "FAIL"))

    # Overall result
    all_passed = (same_seed_hist and final_state_ok and summary_ok and individual_ok and
                  diff_hist and diff_spatial and shape_ok and nan_ok and exec_ok)
    print("validate_reproducibility")
    print("RESULT: " + ("PASS" if all_passed else "FAIL"))
    return all_passed


if __name__ == "__main__":
    sys.exit(0 if test_reproducibility() else 1)