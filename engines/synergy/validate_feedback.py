# validate_feedback.py
"""
Validation of biological feedback loops in the Synergy Engine.

Tests each of the 10 feedback relationships independently by comparing
simulations with low vs high initial values of the causal variable.
"""

import sys
import numpy as np
from engine import SimulationConfig, SynergyEngine


def run_simulation(seed=42, **kwargs):
    """Create config with overrides, run engine, return results."""
    cfg = SimulationConfig(random_seed=seed, **kwargs)
    eng = SynergyEngine(cfg)
    res = eng.run()
    return eng, res


def test_feedback():
    passed_all = True
    base_cfg = {
        "time_steps": 20,
        "dt": 0.1,
        "num_regions": 5,
        "development_mode": False,
        "strict_validation": False,
    }

    # Helper to get final mean of state array from engine
    def final_mean_state(eng, attr):
        arr = getattr(eng, attr)
        return np.mean(arr)

    # ------------------------------------------------------------------
    # Test 1: Metabolic stress → mutation pressure
    # ------------------------------------------------------------------
    eng_low, res_low = run_simulation(initial_metabolic_stress=0.1, **base_cfg)
    eng_high, res_high = run_simulation(initial_metabolic_stress=0.8, **base_cfg)
    mut_low = final_mean_state(eng_low, "mutation_pressure")
    mut_high = final_mean_state(eng_high, "mutation_pressure")
    t1 = mut_high > mut_low
    if not t1:
        passed_all = False
    print("Metabolic stress -> mutation pressure: " + ("PASS" if t1 else "FAIL"))

    # ------------------------------------------------------------------
    # Test 2: Mutation pressure → combined fitness (negative effect)
    # ------------------------------------------------------------------
    eng_low, res_low = run_simulation(initial_mutation_pressure=0.1, **base_cfg)
    eng_high, res_high = run_simulation(initial_mutation_pressure=0.8, **base_cfg)
    fit_low = final_mean_state(eng_low, "combined_fitness")
    fit_high = final_mean_state(eng_high, "combined_fitness")
    t2 = fit_high < fit_low
    if not t2:
        passed_all = False
    print("Mutation pressure -> combined fitness (negative): " + ("PASS" if t2 else "FAIL"))

    # ------------------------------------------------------------------
    # Test 3: Chromatin accessibility → gene expression
    # ------------------------------------------------------------------
    eng_low, res_low = run_simulation(initial_chromatin_accessibility=0.1, **base_cfg)
    eng_high, res_high = run_simulation(initial_chromatin_accessibility=0.8, **base_cfg)
    gene_low = final_mean_state(eng_low, "gene_expression")
    gene_high = final_mean_state(eng_high, "gene_expression")
    t3 = gene_high > gene_low
    if not t3:
        passed_all = False
    print("Chromatin accessibility -> gene expression: " + ("PASS" if t3 else "FAIL"))

    # ------------------------------------------------------------------
    # Test 4: Gene expression → adaptive capacity
    # ------------------------------------------------------------------
    eng_low, res_low = run_simulation(initial_gene_expression=0.1, **base_cfg)
    eng_high, res_high = run_simulation(initial_gene_expression=0.8, **base_cfg)
    adapt_low = final_mean_state(eng_low, "adaptive_capacity")
    adapt_high = final_mean_state(eng_high, "adaptive_capacity")
    t4 = adapt_high > adapt_low
    if not t4:
        passed_all = False
    print("Gene expression -> adaptive capacity: " + ("PASS" if t4 else "FAIL"))

    # ------------------------------------------------------------------
    # Test 5: Mutation pressure → plasticity (positive effect)
    # ------------------------------------------------------------------
    eng_low, res_low = run_simulation(initial_mutation_pressure=0.1, **base_cfg)
    eng_high, res_high = run_simulation(initial_mutation_pressure=0.8, **base_cfg)
    plas_low = final_mean_state(eng_low, "plasticity")
    plas_high = final_mean_state(eng_high, "plasticity")
    t5 = plas_high > plas_low
    if not t5:
        passed_all = False
    print("Mutation pressure -> plasticity: " + ("PASS" if t5 else "FAIL"))

    # ------------------------------------------------------------------
    # Test 6: Resilience → therapy resistance
    # ------------------------------------------------------------------
    eng_low, res_low = run_simulation(initial_cellular_resilience=0.1, **base_cfg)
    eng_high, res_high = run_simulation(initial_cellular_resilience=0.8, **base_cfg)
    resist_low = final_mean_state(eng_low, "therapy_resistance")
    resist_high = final_mean_state(eng_high, "therapy_resistance")
    t6 = resist_high > resist_low
    if not t6:
        passed_all = False
    print("Resilience -> therapy resistance: " + ("PASS" if t6 else "FAIL"))

    # ------------------------------------------------------------------
    # Test 7: Therapy resistance → combined fitness (negative cost)
    # ------------------------------------------------------------------
    eng_low, res_low = run_simulation(initial_therapy_resistance=0.1, **base_cfg)
    eng_high, res_high = run_simulation(initial_therapy_resistance=0.8, **base_cfg)
    fit_res_low = final_mean_state(eng_low, "combined_fitness")
    fit_res_high = final_mean_state(eng_high, "combined_fitness")
    t7 = fit_res_high < fit_res_low
    if not t7:
        passed_all = False
    print("Therapy resistance -> combined fitness (negative): " + ("PASS" if t7 else "FAIL"))

    # ------------------------------------------------------------------
    # Test 8: Hypoxia → metabolic stress
    # ------------------------------------------------------------------
    eng_low, res_low = run_simulation(initial_hypoxia=0.1, **base_cfg)
    eng_high, res_high = run_simulation(initial_hypoxia=0.8, **base_cfg)
    met_stress_low = final_mean_state(eng_low, "metabolic_stress")
    met_stress_high = final_mean_state(eng_high, "metabolic_stress")
    t8 = met_stress_high > met_stress_low
    if not t8:
        passed_all = False
    print("Hypoxia -> metabolic stress: " + ("PASS" if t8 else "FAIL"))

    # ------------------------------------------------------------------
    # Test 9: Oxidative stress → cellular resilience (negative)
    # ------------------------------------------------------------------
    eng_low, res_low = run_simulation(initial_oxidative_stress=0.1, **base_cfg)
    eng_high, res_high = run_simulation(initial_oxidative_stress=0.8, **base_cfg)
    resil_ox_low = final_mean_state(eng_low, "cellular_resilience")
    resil_ox_high = final_mean_state(eng_high, "cellular_resilience")
    t9 = resil_ox_high < resil_ox_low
    if not t9:
        passed_all = False
    print("Oxidative stress -> cellular resilience (negative): " + ("PASS" if t9 else "FAIL"))

    # ------------------------------------------------------------------
    # Test 10: Stemness → cellular resilience (positive)
    # ------------------------------------------------------------------
    eng_low, res_low = run_simulation(initial_stemness=0.1, **base_cfg)
    eng_high, res_high = run_simulation(initial_stemness=0.8, **base_cfg)
    resil_stem_low = final_mean_state(eng_low, "cellular_resilience")
    resil_stem_high = final_mean_state(eng_high, "cellular_resilience")
    t10 = resil_stem_high > resil_stem_low
    if not t10:
        passed_all = False
    print("Stemness -> cellular resilience: " + ("PASS" if t10 else "FAIL"))

    # ------------------------------------------------------------------
    # Determinism: same seed -> identical results
    # ------------------------------------------------------------------
    eng1, res1 = run_simulation(seed=42, **base_cfg)
    eng2, res2 = run_simulation(seed=42, **base_cfg)
    det_ok = True
    for key in ['mean_combined_fitness', 'mean_mutation_pressure',
                'mean_therapy_resistance', 'mean_adaptive_capacity']:
        if getattr(res1, key) != getattr(res2, key):
            det_ok = False
    if det_ok:
        print("Deterministic: PASS")
    else:
        print("Deterministic: FAIL")
        passed_all = False

    # ------------------------------------------------------------------
    # Different seed -> different histories (engine is deterministic but seed changes)
    # ------------------------------------------------------------------
    eng3, res3 = run_simulation(seed=123, **base_cfg)
    diff_ok = (res1.mean_combined_fitness != res3.mean_combined_fitness)
    if diff_ok:
        print("Different seed: PASS")
    else:
        print("Different seed: FAIL")
        passed_all = False

    # ------------------------------------------------------------------
    # Final result
    # ------------------------------------------------------------------
    print("RESULT: " + ("PASS" if passed_all else "FAIL"))
    return passed_all


if __name__ == "__main__":
    sys.exit(0 if test_feedback() else 1)