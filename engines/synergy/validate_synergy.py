# validate_synergy.py
"""
Validation of Synergy Engine core dynamics.

Tests:
1. Combined fitness calculation matches weighted sum.
2. Mutation pressure increases with metabolic stress.
3. Therapy resistance increases with plasticity.
4. Adaptive capacity increases with gene expression.
5. Stemness increases with resilience.
6. System stability: increases with resilience, decreases with mutation pressure.
7. All state variables remain in [0, 1].
8. No NaN or Inf values.
9. All state arrays have correct length.
10. Same seed produces identical histories (determinism).
11. Different seeds produce different histories.
"""

import sys
import numpy as np
from engine import SimulationConfig, SynergyEngine


def run_simulation(seed=42, **kwargs):
    """Create config with overrides, run engine, return engine and results."""
    cfg = SimulationConfig(random_seed=seed, **kwargs)
    eng = SynergyEngine(cfg)
    res = eng.run()
    return eng, res


def test_synergy():
    passed_all = True

    # Base configuration for testing
    base_cfg = {
        "time_steps": 20,
        "dt": 0.1,
        "num_regions": 5,
        "development_mode": False,
    }

    # ------------------------------------------------------------------
    # Test 1: Combined fitness
    # ------------------------------------------------------------------
    eng, _ = run_simulation(**base_cfg)
    # Compute manually from initial state
    tf = eng.tumor_fitness
    mf = eng.metabolic_fitness
    ef = eng.epigenetic_fitness
    w_t = eng.cfg.tumor_fitness_weight
    w_m = eng.cfg.metabolic_fitness_weight
    w_e = eng.cfg.epigenetic_fitness_weight
    manual_combined = w_t * tf + w_m * mf + w_e * ef
    engine_combined = eng.combined_fitness
    combined_ok = np.allclose(manual_combined, engine_combined, rtol=1e-9, atol=1e-9)
    if not combined_ok:
        print("Combined fitness: FAIL (manual calculation mismatch)")
        passed_all = False
    else:
        print("Combined fitness: PASS")

    # ------------------------------------------------------------------
    # Test 2: Mutation pressure vs metabolic stress
    # ------------------------------------------------------------------
    # High metabolic stress initial
    eng_high, res_high = run_simulation(
        initial_metabolic_stress=0.8,
        **base_cfg
    )
    # Low metabolic stress initial
    eng_low, res_low = run_simulation(
        initial_metabolic_stress=0.1,
        **base_cfg
    )
    # Compare mean mutation pressure at final step
    mut_high = np.mean(res_high.mutation_pressure_hist[-1])
    mut_low = np.mean(res_low.mutation_pressure_hist[-1])
    mut_ok = mut_high > mut_low
    if not mut_ok:
        print("Mutation pressure: FAIL (high stress did not increase mutation)")
        passed_all = False
    else:
        print("Mutation pressure: PASS")

    # ------------------------------------------------------------------
    # Test 3: Therapy resistance vs plasticity
    # ------------------------------------------------------------------
    eng_high_plas, res_high_plas = run_simulation(
        initial_plasticity=0.8,
        **base_cfg
    )
    eng_low_plas, res_low_plas = run_simulation(
        initial_plasticity=0.1,
        **base_cfg
    )
    resist_high = np.mean(res_high_plas.therapy_resistance_hist[-1])
    resist_low = np.mean(res_low_plas.therapy_resistance_hist[-1])
    resist_ok = resist_high > resist_low
    if not resist_ok:
        print("Therapy resistance: FAIL (high plasticity did not increase resistance)")
        passed_all = False
    else:
        print("Therapy resistance: PASS")

    # ------------------------------------------------------------------
    # Test 4: Adaptive capacity vs gene expression
    # ------------------------------------------------------------------
    eng_high_gene, res_high_gene = run_simulation(
        initial_gene_expression=0.8,
        **base_cfg
    )
    eng_low_gene, res_low_gene = run_simulation(
        initial_gene_expression=0.1,
        **base_cfg
    )
    adapt_high = np.mean(res_high_gene.adaptive_capacity_hist[-1])
    adapt_low = np.mean(res_low_gene.adaptive_capacity_hist[-1])
    adapt_ok = adapt_high > adapt_low
    if not adapt_ok:
        print("Adaptive capacity: FAIL (high gene expression did not increase adaptive capacity)")
        passed_all = False
    else:
        print("Adaptive capacity: PASS")

    # ------------------------------------------------------------------
    # Test 5: Stemness vs resilience
    # ------------------------------------------------------------------
    eng_high_resil, res_high_resil = run_simulation(
        initial_cellular_resilience=0.8,
        **base_cfg
    )
    eng_low_resil, res_low_resil = run_simulation(
        initial_cellular_resilience=0.1,
        **base_cfg
    )
    stem_high = np.mean(res_high_resil.stemness_hist[-1])
    stem_low = np.mean(res_low_resil.stemness_hist[-1])
    stem_ok = stem_high > stem_low
    if not stem_ok:
        print("Stemness: FAIL (high resilience did not increase stemness)")
        passed_all = False
    else:
        print("Stemness: PASS")

    # ------------------------------------------------------------------
    # Test 6: System stability
    # ------------------------------------------------------------------
    # a) increasing resilience increases stability
    eng_high_resil2, res_high_resil2 = run_simulation(
        initial_cellular_resilience=0.8,
        **base_cfg
    )
    eng_low_resil2, res_low_resil2 = run_simulation(
        initial_cellular_resilience=0.1,
        **base_cfg
    )
    stab_high = np.mean(res_high_resil2.system_stability_hist[-1])
    stab_low = np.mean(res_low_resil2.system_stability_hist[-1])
    stab_resil_ok = stab_high > stab_low

    # b) increasing mutation pressure decreases stability
    eng_high_mut, res_high_mut = run_simulation(
        initial_mutation_pressure=0.8,
        **base_cfg
    )
    eng_low_mut, res_low_mut = run_simulation(
        initial_mutation_pressure=0.1,
        **base_cfg
    )
    stab_mut_high = np.mean(res_high_mut.system_stability_hist[-1])
    stab_mut_low = np.mean(res_low_mut.system_stability_hist[-1])
    stab_mut_ok = stab_mut_high < stab_mut_low

    stab_ok = stab_resil_ok and stab_mut_ok
    if not stab_ok:
        print("System stability: FAIL (did not meet both criteria)")
        passed_all = False
    else:
        print("System stability: PASS")

    # ------------------------------------------------------------------
    # Test 7: Bounded variables
    # ------------------------------------------------------------------
    eng, res = run_simulation(**base_cfg)
    bounded_ok = True
    for attr in [
        "tumor_fitness", "metabolic_fitness", "epigenetic_fitness",
        "combined_fitness", "stemness", "plasticity", "mutation_pressure",
        "selection_pressure", "metabolic_stress", "oxidative_stress",
        "hypoxia", "chromatin_accessibility", "gene_expression",
        "adaptive_capacity", "therapy_resistance", "cellular_resilience",
        "system_stability"
    ]:
        arr = getattr(eng, attr)
        if np.any(arr < 0) or np.any(arr > 1):
            bounded_ok = False
            print(f"  {attr} out of bounds")
    if not bounded_ok:
        print("Bounded variables: FAIL")
        passed_all = False
    else:
        print("Bounded variables: PASS")

    # ------------------------------------------------------------------
    # Test 8: Finite values
    # ------------------------------------------------------------------
    finite_ok = True
    for attr in [
        "tumor_fitness", "metabolic_fitness", "epigenetic_fitness",
        "combined_fitness", "stemness", "plasticity", "mutation_pressure",
        "selection_pressure", "metabolic_stress", "oxidative_stress",
        "hypoxia", "chromatin_accessibility", "gene_expression",
        "adaptive_capacity", "therapy_resistance", "cellular_resilience",
        "system_stability"
    ]:
        arr = getattr(eng, attr)
        if not np.all(np.isfinite(arr)):
            finite_ok = False
            print(f"  {attr} contains non-finite values")
    if not finite_ok:
        print("Finite values: FAIL")
        passed_all = False
    else:
        print("Finite values: PASS")

    # ------------------------------------------------------------------
    # Test 9: Array sizes
    # ------------------------------------------------------------------
    size_ok = True
    n = eng.cfg.num_regions
    for attr in [
        "tumor_fitness", "metabolic_fitness", "epigenetic_fitness",
        "combined_fitness", "stemness", "plasticity", "mutation_pressure",
        "selection_pressure", "metabolic_stress", "oxidative_stress",
        "hypoxia", "chromatin_accessibility", "gene_expression",
        "adaptive_capacity", "therapy_resistance", "cellular_resilience",
        "system_stability"
    ]:
        arr = getattr(eng, attr)
        if arr.shape != (n,):
            size_ok = False
            print(f"  {attr} shape {arr.shape} != ({n},)")
    if not size_ok:
        print("Array sizes: FAIL")
        passed_all = False
    else:
        print("Array sizes: PASS")

    # ------------------------------------------------------------------
    # Test 10: Determinism
    # ------------------------------------------------------------------
    eng1, res1 = run_simulation(seed=42, **base_cfg)
    eng2, res2 = run_simulation(seed=42, **base_cfg)
    # Compare all scalar metric histories
    det_ok = True
    for key in ['mean_combined_fitness', 'mean_mutation_pressure',
                'mean_therapy_resistance', 'mean_adaptive_capacity',
                'mean_resilience', 'mean_stability', 'mean_stemness',
                'mean_plasticity', 'mean_metabolic_stress',
                'mean_oxidative_stress', 'mean_hypoxia']:
        if getattr(res1, key) != getattr(res2, key):
            det_ok = False
            print(f"  {key} differs between same-seed runs")
    # Also compare a few spatial histories (e.g., first step)
    for hist_key in ['tumor_fitness_hist', 'mutation_pressure_hist']:
        h1 = getattr(res1, hist_key)
        h2 = getattr(res2, hist_key)
        if not all(np.array_equal(a, b) for a, b in zip(h1, h2)):
            det_ok = False
            print(f"  {hist_key} differs between same-seed runs")
    if not det_ok:
        print("Deterministic: FAIL")
        passed_all = False
    else:
        print("Deterministic: PASS")

    # ------------------------------------------------------------------
    # Test 11: Different seeds
    # ------------------------------------------------------------------
    eng3, res3 = run_simulation(seed=123, **base_cfg)
    diff_ok = False
    # Compare mean_combined_fitness lists; they should differ
    if res1.mean_combined_fitness != res3.mean_combined_fitness:
        diff_ok = True
    if not diff_ok:
        print("Different seed: FAIL (histories identical)")
        passed_all = False
    else:
        print("Different seed: PASS")

    # ------------------------------------------------------------------
    # Final result
    # ------------------------------------------------------------------
    print("RESULT: " + ("PASS" if passed_all else "FAIL"))
    return passed_all


if __name__ == "__main__":
    sys.exit(0 if test_synergy() else 1)