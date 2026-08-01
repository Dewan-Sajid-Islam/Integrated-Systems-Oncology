# validate_phenotypes.py
"""
Validation of phenotype assignment.

This validator tests that the engine correctly classifies regions into each
metabolic phenotype based on the state variables. It creates synthetic
states for each phenotype and verifies the engine's classification.

Tests:
- Each phenotype (OXIDATIVE, GLYCOLYTIC, INTERMEDIATE, HYPOXIC, QUIESCENT, NECROTIC)
  is correctly assigned.
- No invalid phenotype values.
- Phenotype counts sum to num_regions.
- Deterministic execution.
"""

import sys
import numpy as np
from engine import SimulationConfig, MetabolismEngine, MetabolicPhenotype


def test_phenotype_assignment():
    # Use a minimal configuration: extremely small dt so that state changes are negligible.
    cfg = SimulationConfig(
        random_seed=42,
        time_steps=1,
        dt=1e-9,                      # effectively zero, but still >0
        num_regions=6,
        vascular_density=0.0,
        oxygen_consumption_rate=0.0,
        glucose_consumption_rate=0.0,
        diffusion_oxygen=0.0,
        diffusion_glucose=0.0,
        diffusion_lactate=0.0,
        diffusion_ph=0.0,
        glycolytic_atp_yield=0.0,
        oxidative_atp_yield=0.0,
        lactate_production_rate=0.0,
        warburg_bias=0.0,
        aerobic_glycolysis_fraction=0.0,
        mitochondrial_efficiency_base=1.0,
        ph_acidification_rate=0.0,
        ph_buffering=0.0,
        ros_production_rate=0.0,
        ros_decay_rate=0.0,
        development_mode=False,
        strict_validation=False,
        initial_oxygen=0.0,
        initial_glucose=0.0,
        initial_lactate=0.0,
        initial_atp=1.0,
        initial_ph=7.4,
        initial_ros=0.0,
        necrosis_atp_threshold=0.2,
        necrosis_stress_threshold=0.8,
        necrosis_duration_threshold=1,
        oxidative_oxygen_threshold=0.3,
        hypoxic_oxygen_threshold=0.1,
        high_atp_threshold=0.6,
        low_atp_threshold=0.3,
    )
    eng = MetabolismEngine(cfg)
    eng.initialize_state()

    # Manually set the state for each region to force a specific phenotype.
    # Region 0: OXIDATIVE - high oxygen, high ATP
    # Region 1: GLYCOLYTIC - moderate oxygen, high stress (lactate/acidosis)
    # Region 2: INTERMEDIATE - moderate oxygen, moderate ATP, low stress (stress < 0.3)
    # Region 3: HYPOXIC - low oxygen (below hypoxic threshold)
    # Region 4: QUIESCENT - low ATP (below low_atp_threshold)
    # Region 5: NECROTIC - set necrotic flag

    # Adjust Region 2 to have stress < 0.3: increase ATP, decrease lactate, increase pH.
    eng.oxygen = np.array([0.5, 0.3, 0.3, 0.05, 0.3, 0.0])
    eng.atp = np.array([0.8, 0.5, 0.6, 0.5, 0.1, 0.0])      # Region 2: ATP=0.6
    eng.lactate = np.array([0.0, 0.6, 0.05, 0.1, 0.1, 0.0])  # Region 2: lactate=0.05
    eng.ph = np.array([7.4, 6.8, 7.3, 7.2, 7.2, 7.4])        # Region 2: pH=7.3
    eng.necrotic = np.array([False, False, False, False, False, True])

    # Compute stress manually using the engine's formula (to mimic its internal computation)
    # atp_deficit = max(0, 1 - ATP/initial_atp)
    # lactate_stress = clamp(lactate/0.5, 0, 1)
    # ph_stress = clamp((7.4 - pH)/1.0, 0, 1)
    # stress = 0.4*atp_deficit + 0.3*lactate_stress + 0.3*ph_stress
    initial_atp = cfg.initial_atp
    if initial_atp <= 0:
        atp_deficit = np.zeros(eng.cfg.num_regions)
    else:
        atp_deficit = np.maximum(0.0, 1.0 - eng.atp / initial_atp)
    lactate_stress = np.clip(eng.lactate / 0.5, 0.0, 1.0)
    ph_stress = np.clip((7.4 - eng.ph) / 1.0, 0.0, 1.0)
    eng.stress = 0.4 * atp_deficit + 0.3 * lactate_stress + 0.3 * ph_stress

    # Call _step() to run phenotype assignment. With dt extremely small,
    # state changes are negligible, but phenotype logic will be applied.
    eng._step()

    # Expected phenotypes:
    # Region 0: OXIDATIVE (oxygen > 0.3, ATP > 0.6) -> OXIDATIVE
    # Region 1: GLYCOLYTIC (oxygen > 0.1, ATP not low, stress > 0.3) -> GLYCOLYTIC
    # Region 2: INTERMEDIATE (oxygen > 0.1, ATP not low, stress <= 0.3) -> INTERMEDIATE
    # Region 3: HYPOXIC (oxygen < 0.1) -> HYPOXIC
    # Region 4: QUIESCENT (ATP < 0.3) -> QUIESCENT
    # Region 5: NECROTIC (necrotic flag) -> NECROTIC
    expected = [
        MetabolicPhenotype.OXIDATIVE,
        MetabolicPhenotype.GLYCOLYTIC,
        MetabolicPhenotype.INTERMEDIATE,
        MetabolicPhenotype.HYPOXIC,
        MetabolicPhenotype.QUIESCENT,
        MetabolicPhenotype.NECROTIC
    ]

    passed = True
    print("validate_phenotypes")
    print("  Region | Oxygen | ATP | Lactate | pH   | Stress | Phenotype (expected)")
    for i in range(cfg.num_regions):
        exp_name = MetabolicPhenotype(expected[i]).name
        got_name = MetabolicPhenotype(eng.phenotype[i]).name
        ok = (eng.phenotype[i] == expected[i])
        if not ok:
            passed = False
        status = "OK" if ok else "FAIL"
        print(f"    {i:2d}   | {eng.oxygen[i]:6.3f} | {eng.atp[i]:5.3f} | {eng.lactate[i]:7.3f} | {eng.ph[i]:5.3f} | {eng.stress[i]:7.4f} | {got_name:12s} ({exp_name}) {status}")

    # Check that phenotype counts sum to num_regions
    counts = {int(p): 0 for p in MetabolicPhenotype}
    for phen in eng.phenotype:
        counts[int(phen)] = counts.get(int(phen), 0) + 1
    sum_ok = sum(counts.values()) == cfg.num_regions

    if not sum_ok:
        print(f"  Phenotype counts sum to {sum(counts.values())}, expected {cfg.num_regions}")
        passed = False

    # Determinism: run twice with same seed; should produce same phenotype assignments.
    eng2 = MetabolismEngine(cfg)
    eng2.initialize_state()
    # Set same state
    eng2.oxygen = eng.oxygen.copy()
    eng2.atp = eng.atp.copy()
    eng2.lactate = eng.lactate.copy()
    eng2.ph = eng.ph.copy()
    eng2.necrotic = eng.necrotic.copy()
    # Compute stress
    if initial_atp <= 0:
        atp_deficit2 = np.zeros(cfg.num_regions)
    else:
        atp_deficit2 = np.maximum(0.0, 1.0 - eng2.atp / initial_atp)
    lactate_stress2 = np.clip(eng2.lactate / 0.5, 0.0, 1.0)
    ph_stress2 = np.clip((7.4 - eng2.ph) / 1.0, 0.0, 1.0)
    eng2.stress = 0.4 * atp_deficit2 + 0.3 * lactate_stress2 + 0.3 * ph_stress2
    eng2._step()
    deterministic = np.array_equal(eng.phenotype, eng2.phenotype)
    if not deterministic:
        print("  Determinism failed: phenotype differs on second run")
        passed = False

    print(f"  All phenotypes correctly assigned: {passed}")
    print(f"  Counts sum to num_regions: {sum_ok}")
    print(f"  Deterministic: {deterministic}")
    print(f"  RESULT: {'PASS' if passed else 'FAIL'}")
    return passed


if __name__ == "__main__":
    sys.exit(0 if test_phenotype_assignment() else 1)