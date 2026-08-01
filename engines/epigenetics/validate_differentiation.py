# validate_differentiation.py
"""
Validation of differentiation state classification.

This validator constructs synthetic states and verifies the engine's
differentiation state assignment.

Tests:
- UNDIFFERENTIATED for diff < 0.2.
- PROGENITOR for 0.2 <= diff < 0.5.
- DIFFERENTIATED for 0.5 <= diff < 0.8.
- TERMINALLY_DIFFERENTIATED for diff >= 0.8.
- Higher stemness leads to lower differentiation (but we check classification based on diff).
- Plasticity can allow dedifferentiation (not directly tested here).
- Counts sum to num_regions.
- Deterministic execution.
"""

import sys
import numpy as np
from engine import SimulationConfig, EpigeneticsEngine, DifferentiationState


def test_differentiation():
    # Minimal config with zero dt.
    cfg = SimulationConfig(
        random_seed=42,
        time_steps=1,
        dt=1e-9,
        num_regions=4,
        development_mode=False,
        strict_validation=False,
        methylation_drift_rate=0.0,
        demethylation_rate=0.0,
        acetylation_rate=0.0,
        deacetylation_rate=0.0,
        accessibility_opening_rate=0.0,
        accessibility_closing_rate=0.0,
        instability_base=0.0,
        instability_stress_factor=0.0,
        plasticity_base=0.0,
        plasticity_instability_factor=0.0,
        stemness_differentiation_rate=0.0,
        differentiation_rate=0.0,
        age_accumulation_rate=0.0,
        stress_base=0.0,
        stress_instability_factor=0.0,
    )
    eng = EpigeneticsEngine(cfg)
    eng.initialize_state()

    # Manually set differentiation values and also stemness to test the logic (though assignment is based on diff).
    # Region 0: UNDIFFERENTIATED (diff = 0.0)
    # Region 1: PROGENITOR (diff = 0.35)
    # Region 2: DIFFERENTIATED (diff = 0.65)
    # Region 3: TERMINALLY_DIFFERENTIATED (diff = 0.9)

    eng.differentiation = np.array([0.0, 0.35, 0.65, 0.9])
    # Set stemness arbitrarily
    eng.stemness = np.array([0.9, 0.5, 0.2, 0.05])

    # Call _step to update discrete states (no change in state values)
    eng._step()

    expected = [
        DifferentiationState.UNDIFFERENTIATED,
        DifferentiationState.PROGENITOR,
        DifferentiationState.DIFFERENTIATED,
        DifferentiationState.TERMINALLY_DIFFERENTIATED
    ]

    passed = True
    for i, exp in enumerate(expected):
        got = DifferentiationState(eng.diff_state[i])
        ok = (got == exp)
        if not ok:
            print(f"  Region {i}: diff={eng.differentiation[i]:.2f}, expected {exp.name}, got {got.name}")
            passed = False

    # Check counts sum to num_regions
    counts = {int(v): 0 for v in DifferentiationState}
    for state in eng.diff_state:
        counts[int(state)] = counts.get(int(state), 0) + 1
    sum_ok = sum(counts.values()) == cfg.num_regions
    if not sum_ok:
        print(f"  Differentiation state counts sum to {sum(counts.values())}, expected {cfg.num_regions}")
        passed = False

    # Determinism
    eng2 = EpigeneticsEngine(cfg)
    eng2.initialize_state()
    eng2.differentiation = eng.differentiation.copy()
    eng2.stemness = eng.stemness.copy()
    eng2._step()
    deterministic = np.array_equal(eng.diff_state, eng2.diff_state)
    if not deterministic:
        print("  Determinism failed")
        passed = False

    # Additionally, verify that higher stemness -> lower differentiation (trend)
    # We can check that stemness is inversely related to diff (but not a direct test).
    # We'll just check that the state assignment is correct.

    print("validate_differentiation")
    print(f"  All differentiation states correctly assigned: {passed}")
    print(f"  Counts sum to num_regions: {sum_ok}")
    print(f"  Deterministic: {deterministic}")
    print(f"  RESULT: {'PASS' if passed else 'FAIL'}")
    return passed


if __name__ == "__main__":
    sys.exit(0 if test_differentiation() else 1)