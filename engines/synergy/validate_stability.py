# validate_stability.py
"""
Validation of numerical and biological stability of the Synergy Engine.

Tests:
1. All state variables are finite.
2. No NaN values in any history.
3. No Inf values.
4. All bounded variables remain within [0, 1].
5. Combined fitness remains within [0, 1].
6. Mutation pressure never negative.
7. Therapy resistance never negative.
8. Cellular resilience never negative.
9. Plasticity never negative.
10. System stability remains bounded [0, 1].
11. Long simulations (500 steps) remain stable.
12. Mean values remain finite throughout histories.
13. Array shapes remain constant.
14. Deterministic: same seed yields identical results.
15. Different seeds yield different histories when stochasticity exists.
"""

import sys
import numpy as np
from engine import SimulationConfig, SynergyEngine


def run_simulation(seed=42, time_steps=20, **kwargs):
    """Run engine with given config, return engine and results."""
    cfg = SimulationConfig(random_seed=seed, time_steps=time_steps, **kwargs)
    eng = SynergyEngine(cfg)
    res = eng.run()
    return eng, res


def check_array(arr, name):
    """Check array for finite, non-negative, bounded [0,1] if applicable."""
    ok = True
    if not np.all(np.isfinite(arr)):
        print(f"  {name} contains non-finite values")
        ok = False
    if np.any(arr < 0):
        print(f"  {name} has negative values")
        ok = False
    # For bounded variables (those that should stay in [0,1])
    if name in ["tumor_fitness", "metabolic_fitness", "epigenetic_fitness",
                "combined_fitness", "stemness", "plasticity", "mutation_pressure",
                "selection_pressure", "metabolic_stress", "oxidative_stress",
                "hypoxia", "chromatin_accessibility", "gene_expression",
                "adaptive_capacity", "therapy_resistance", "cellular_resilience",
                "system_stability"]:
        if np.any(arr < 0) or np.any(arr > 1):
            print(f"  {name} out of [0,1] range")
            ok = False
    return ok


def test_stability():
    passed_all = True
    # Use a moderate config but with long time steps to test stability
    base_cfg = {
        "time_steps": 50,
        "dt": 0.1,
        "num_regions": 10,
        "development_mode": False,
        "strict_validation": False,
    }

    # Run a simulation with default parameters
    eng, res = run_simulation(**base_cfg)

    # List of state variable names (excluding internal arrays)
    state_vars = [
        "tumor_fitness", "metabolic_fitness", "epigenetic_fitness",
        "combined_fitness", "stemness", "plasticity", "mutation_pressure",
        "selection_pressure", "metabolic_stress", "oxidative_stress",
        "hypoxia", "chromatin_accessibility", "gene_expression",
        "adaptive_capacity", "therapy_resistance", "cellular_resilience",
        "system_stability"
    ]

    # Test 1-4, 6-10: Check each state array for finite, non-negative, bounded.
    state_ok = True
    for var in state_vars:
        arr = getattr(eng, var)
        if not check_array(arr, var):
            state_ok = False
    if state_ok:
        print("State variables finite, non-negative, bounded: PASS")
    else:
        print("State variables finite, non-negative, bounded: FAIL")
        passed_all = False

    # Test 5: Combined fitness (already covered in state check, but we check separately)
    cf = eng.combined_fitness
    if np.all(np.isfinite(cf)) and np.all(cf >= 0) and np.all(cf <= 1):
        print("Combined fitness within bounds: PASS")
    else:
        print("Combined fitness within bounds: FAIL")
        passed_all = False

    # Test 11: Long simulation (500 steps) remains stable
    long_cfg = {**base_cfg, "time_steps": 500}
    eng_long, res_long = run_simulation(**long_cfg)
    long_ok = True
    for var in state_vars:
        arr = getattr(eng_long, var)
        if not np.all(np.isfinite(arr)):
            long_ok = False
            print(f"  Long simulation: {var} has non-finite values")
            break
        if var in ["mutation_pressure", "therapy_resistance", "cellular_resilience",
                   "plasticity", "combined_fitness"] + [v for v in state_vars if v not in ["combined_fitness"]]:
            # All should be >=0 and for bounded vars <=1
            if np.any(arr < 0) or np.any(arr > 1):
                long_ok = False
                print(f"  Long simulation: {var} out of bounds")
                break
    if long_ok:
        print("Long simulation (500 steps) stable: PASS")
    else:
        print("Long simulation (500 steps) stable: FAIL")
        passed_all = False

    # Test 12: Mean values remain finite throughout histories
    # Check all scalar metric lists
    mean_keys = [
        'mean_combined_fitness', 'mean_mutation_pressure', 'mean_therapy_resistance',
        'mean_adaptive_capacity', 'mean_resilience', 'mean_stability',
        'mean_stemness', 'mean_plasticity', 'mean_metabolic_stress',
        'mean_oxidative_stress', 'mean_hypoxia'
    ]
    means_ok = True
    for key in mean_keys:
        hist = getattr(res, key)
        if not all(np.isfinite(v) for v in hist):
            means_ok = False
            print(f"  {key} contains non-finite values")
    if means_ok:
        print("Mean values finite throughout histories: PASS")
    else:
        print("Mean values finite throughout histories: FAIL")
        passed_all = False

    # Test 13: Array shapes remain constant (check histories)
    shape_ok = True
    n_regions = eng.cfg.num_regions
    for hist_name in [
        'tumor_fitness_hist', 'metabolic_fitness_hist', 'epigenetic_fitness_hist',
        'combined_fitness_hist', 'stemness_hist', 'plasticity_hist',
        'mutation_pressure_hist', 'selection_pressure_hist', 'metabolic_stress_hist',
        'oxidative_stress_hist', 'hypoxia_hist', 'chromatin_accessibility_hist',
        'gene_expression_hist', 'adaptive_capacity_hist', 'therapy_resistance_hist',
        'cellular_resilience_hist', 'system_stability_hist'
    ]:
        hist = getattr(res, hist_name)
        for arr in hist:
            if arr.shape != (n_regions,):
                shape_ok = False
                print(f"  {hist_name} has incorrect shape {arr.shape}")
                break
        if not shape_ok:
            break
    if shape_ok:
        print("Array shapes constant: PASS")
    else:
        print("Array shapes constant: FAIL")
        passed_all = False

    # Test 14: Deterministic execution (same seed yields identical results)
    eng1, res1 = run_simulation(seed=42, **base_cfg)
    eng2, res2 = run_simulation(seed=42, **base_cfg)
    det_ok = True
    for key in mean_keys:
        if getattr(res1, key) != getattr(res2, key):
            det_ok = False
            print(f"  {key} differs between same-seed runs")
            break
    if det_ok:
        print("Deterministic (same seed): PASS")
    else:
        print("Deterministic (same seed): FAIL")
        passed_all = False

    # Test 15: Different seeds produce different histories (if stochasticity exists)
    # The engine has no stochasticity (all RNG usage is for initial heterogeneity,
    # which is deterministic given the seed). So different seeds should produce different
    # histories because the heterogeneity mask differs. We check that mean_combined_fitness
    # histories differ.
    eng3, res3 = run_simulation(seed=123, **base_cfg)
    diff_ok = (res1.mean_combined_fitness != res3.mean_combined_fitness)
    if diff_ok:
        print("Different seed: histories differ (PASS)")
    else:
        print("Different seed: histories identical (FAIL)")
        passed_all = False

    # Additional check: ensure no NaN/Inf in any history array
    nan_ok = True
    for hist_name in [
        'tumor_fitness_hist', 'metabolic_fitness_hist', 'epigenetic_fitness_hist',
        'combined_fitness_hist', 'stemness_hist', 'plasticity_hist',
        'mutation_pressure_hist', 'selection_pressure_hist', 'metabolic_stress_hist',
        'oxidative_stress_hist', 'hypoxia_hist', 'chromatin_accessibility_hist',
        'gene_expression_hist', 'adaptive_capacity_hist', 'therapy_resistance_hist',
        'cellular_resilience_hist', 'system_stability_hist'
    ]:
        hist = getattr(res, hist_name)
        for arr in hist:
            if not np.all(np.isfinite(arr)):
                nan_ok = False
                print(f"  {hist_name} contains non-finite values")
                break
        if not nan_ok:
            break
    if nan_ok:
        print("No NaN/Inf in histories: PASS")
    else:
        print("No NaN/Inf in histories: FAIL")
        passed_all = False

    # Final result
    print("validate_stability")
    print("RESULT: " + ("PASS" if passed_all else "FAIL"))
    return passed_all


if __name__ == "__main__":
    sys.exit(0 if test_stability() else 1)