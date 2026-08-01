# validate_adaptation.py
"""
Validation of adaptive dynamics in the Synergy Engine.

Tests actual implemented relationships:
1. Higher mutation pressure → higher adaptive capacity (indirect chain)
2. Higher gene expression → higher adaptive capacity
3. Higher chromatin accessibility → higher gene expression
4. Higher plasticity → higher chromatin accessibility
5. Higher stemness → higher cellular resilience
6. Higher cellular resilience → higher therapy resistance
7. Higher cellular resilience → higher system stability
8. Higher metabolic stress → lower combined fitness
9. Higher oxidative stress → lower combined fitness
10. Higher therapy resistance → lower combined fitness (cost)
11. Adaptive variables remain finite
12. Adaptive variables remain bounded [0, 1]
13. Mean adaptive metrics evolve smoothly without numerical instability
14. Same seed yields identical adaptive histories
15. Different seeds yield different adaptive histories
"""

import sys
import numpy as np
from engine import SimulationConfig, SynergyEngine


def run_simulation(seed=42, time_steps=20, **kwargs):
    cfg = SimulationConfig(random_seed=seed, time_steps=time_steps, **kwargs)
    eng = SynergyEngine(cfg)
    res = eng.run()
    return eng, res


def final_mean(eng, attr):
    return np.mean(getattr(eng, attr))


def compare_high_low(high_val, low_val, relation):
    """Compare high and low final means; relation is '>' or '<'."""
    if relation == '>':
        return high_val > low_val
    elif relation == '<':
        return high_val < low_val
    else:
        return False


def test_adaptation():
    passed_all = True
    base_cfg = {
        "time_steps": 30,
        "dt": 0.1,
        "num_regions": 5,
        "development_mode": False,
        "strict_validation": False,
    }

    # ------------------------------------------------------------------
    # Test 1: Mutation pressure -> adaptive capacity (indirect)
    # ------------------------------------------------------------------
    eng_low, _ = run_simulation(initial_mutation_pressure=0.1, **base_cfg)
    eng_high, _ = run_simulation(initial_mutation_pressure=0.8, **base_cfg)
    t1 = final_mean(eng_high, "adaptive_capacity") > final_mean(eng_low, "adaptive_capacity")
    print("Mutation pressure -> adaptive capacity: " + ("PASS" if t1 else "FAIL"))

    # ------------------------------------------------------------------
    # Test 2: Gene expression -> adaptive capacity
    # ------------------------------------------------------------------
    eng_low, _ = run_simulation(initial_gene_expression=0.1, **base_cfg)
    eng_high, _ = run_simulation(initial_gene_expression=0.8, **base_cfg)
    t2 = final_mean(eng_high, "adaptive_capacity") > final_mean(eng_low, "adaptive_capacity")
    print("Gene expression -> adaptive capacity: " + ("PASS" if t2 else "FAIL"))

    # ------------------------------------------------------------------
    # Test 3: Chromatin accessibility -> gene expression
    # ------------------------------------------------------------------
    eng_low, _ = run_simulation(initial_chromatin_accessibility=0.1, **base_cfg)
    eng_high, _ = run_simulation(initial_chromatin_accessibility=0.8, **base_cfg)
    t3 = final_mean(eng_high, "gene_expression") > final_mean(eng_low, "gene_expression")
    print("Chromatin accessibility -> gene expression: " + ("PASS" if t3 else "FAIL"))

    # ------------------------------------------------------------------
    # Test 4: Plasticity -> chromatin accessibility
    # ------------------------------------------------------------------
    eng_low, _ = run_simulation(initial_plasticity=0.1, **base_cfg)
    eng_high, _ = run_simulation(initial_plasticity=0.8, **base_cfg)
    t4 = final_mean(eng_high, "chromatin_accessibility") > final_mean(eng_low, "chromatin_accessibility")
    print("Plasticity -> chromatin accessibility: " + ("PASS" if t4 else "FAIL"))

    # ------------------------------------------------------------------
    # Test 5: Stemness -> cellular resilience
    # ------------------------------------------------------------------
    eng_low, _ = run_simulation(initial_stemness=0.1, **base_cfg)
    eng_high, _ = run_simulation(initial_stemness=0.8, **base_cfg)
    t5 = final_mean(eng_high, "cellular_resilience") > final_mean(eng_low, "cellular_resilience")
    print("Stemness -> cellular resilience: " + ("PASS" if t5 else "FAIL"))

    # ------------------------------------------------------------------
    # Test 6: Cellular resilience -> therapy resistance
    # ------------------------------------------------------------------
    eng_low, _ = run_simulation(initial_cellular_resilience=0.1, **base_cfg)
    eng_high, _ = run_simulation(initial_cellular_resilience=0.8, **base_cfg)
    t6 = final_mean(eng_high, "therapy_resistance") > final_mean(eng_low, "therapy_resistance")
    print("Resilience -> therapy resistance: " + ("PASS" if t6 else "FAIL"))

    # ------------------------------------------------------------------
    # Test 7: Cellular resilience -> system stability
    # ------------------------------------------------------------------
    eng_low, _ = run_simulation(initial_cellular_resilience=0.1, **base_cfg)
    eng_high, _ = run_simulation(initial_cellular_resilience=0.8, **base_cfg)
    t7 = final_mean(eng_high, "system_stability") > final_mean(eng_low, "system_stability")
    print("Resilience -> system stability: " + ("PASS" if t7 else "FAIL"))

    # ------------------------------------------------------------------
    # Test 8: Metabolic stress -> combined fitness (negative)
    # ------------------------------------------------------------------
    eng_low, _ = run_simulation(initial_metabolic_stress=0.1, **base_cfg)
    eng_high, _ = run_simulation(initial_metabolic_stress=0.8, **base_cfg)
    t8 = final_mean(eng_high, "combined_fitness") < final_mean(eng_low, "combined_fitness")
    print("Metabolic stress -> combined fitness (negative): " + ("PASS" if t8 else "FAIL"))

    # ------------------------------------------------------------------
    # Test 9: Oxidative stress -> combined fitness (negative)
    # ------------------------------------------------------------------
    eng_low, _ = run_simulation(initial_oxidative_stress=0.1, **base_cfg)
    eng_high, _ = run_simulation(initial_oxidative_stress=0.8, **base_cfg)
    t9 = final_mean(eng_high, "combined_fitness") < final_mean(eng_low, "combined_fitness")
    print("Oxidative stress -> combined fitness (negative): " + ("PASS" if t9 else "FAIL"))

    # ------------------------------------------------------------------
    # Test 10: Therapy resistance -> combined fitness (negative cost)
    # ------------------------------------------------------------------
    eng_low, _ = run_simulation(initial_therapy_resistance=0.1, **base_cfg)
    eng_high, _ = run_simulation(initial_therapy_resistance=0.8, **base_cfg)
    t10 = final_mean(eng_high, "combined_fitness") < final_mean(eng_low, "combined_fitness")
    print("Therapy resistance -> combined fitness (negative): " + ("PASS" if t10 else "FAIL"))

    # ------------------------------------------------------------------
    # Test 11: Adaptive variables remain finite (check histories)
    # ------------------------------------------------------------------
    _, res = run_simulation(**base_cfg)
    adapt_vars = ['adaptive_capacity', 'gene_expression', 'chromatin_accessibility', 'plasticity']
    finite_ok = True
    for var in adapt_vars:
        hist = getattr(res, var + '_hist')
        for arr in hist:
            if not np.all(np.isfinite(arr)):
                finite_ok = False
                break
        if not finite_ok:
            break
    print("Adaptive variables finite: " + ("PASS" if finite_ok else "FAIL"))

    # ------------------------------------------------------------------
    # Test 12: Adaptive variables bounded [0,1]
    # ------------------------------------------------------------------
    bounded_ok = True
    for var in adapt_vars:
        hist = getattr(res, var + '_hist')
        for arr in hist:
            if np.any(arr < 0) or np.any(arr > 1):
                bounded_ok = False
                break
        if not bounded_ok:
            break
    print("Adaptive variables bounded: " + ("PASS" if bounded_ok else "FAIL"))

    # ------------------------------------------------------------------
    # Test 13: Mean adaptive metrics evolve smoothly (no large jumps)
    # ------------------------------------------------------------------
    smooth_ok = True
    for key in ['mean_adaptive_capacity', 'mean_plasticity', 'mean_stemness']:
        hist = getattr(res, key)
        diffs = np.diff(hist)
        if np.any(np.abs(diffs) > 0.5):  # arbitrary threshold for stability
            smooth_ok = False
            break
    print("Adaptive metrics smooth: " + ("PASS" if smooth_ok else "FAIL"))

    # ------------------------------------------------------------------
    # Test 14: Same seed yields identical histories
    # ------------------------------------------------------------------
    _, res1 = run_simulation(seed=42, **base_cfg)
    _, res2 = run_simulation(seed=42, **base_cfg)
    det_ok = True
    for key in ['mean_adaptive_capacity', 'mean_plasticity', 'mean_stemness']:
        if getattr(res1, key) != getattr(res2, key):
            det_ok = False
            break
    print("Deterministic (same seed): " + ("PASS" if det_ok else "FAIL"))

    # ------------------------------------------------------------------
    # Test 15: Different seeds yield different histories
    # ------------------------------------------------------------------
    _, res3 = run_simulation(seed=123, **base_cfg)
    diff_ok = (res1.mean_adaptive_capacity != res3.mean_adaptive_capacity)
    print("Different seeds: " + ("PASS" if diff_ok else "FAIL"))

    # ------------------------------------------------------------------
    # Long simulation stability (500 steps)
    # ------------------------------------------------------------------
    long_cfg = {**base_cfg, "time_steps": 500}
    eng_long, res_long = run_simulation(**long_cfg)
    long_ok = True
    for var in ['adaptive_capacity', 'gene_expression', 'chromatin_accessibility', 'plasticity']:
        arr = getattr(eng_long, var)
        if not np.all(np.isfinite(arr)) or np.any(arr < 0) or np.any(arr > 1):
            long_ok = False
            break
    print("Long simulation (500 steps): " + ("PASS" if long_ok else "FAIL"))

    # ------------------------------------------------------------------
    # Final result
    # ------------------------------------------------------------------
    all_passed = all([t1, t2, t3, t4, t5, t6, t7, t8, t9, t10,
                      finite_ok, bounded_ok, smooth_ok, det_ok, diff_ok, long_ok])
    print("validate_adaptation")
    print("RESULT: " + ("PASS" if all_passed else "FAIL"))
    return all_passed


if __name__ == "__main__":
    sys.exit(0 if test_adaptation() else 1)