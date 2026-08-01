# validate_chromatin.py
"""
Validation of chromatin state classification.

This validator tests the engine's actual classification logic:
- Chromatin state is based solely on accessibility (acc).
- acc < 0.3  -> CLOSED
- 0.3 <= acc < 0.7 -> INTERMEDIATE
- acc >= 0.7 -> OPEN

It constructs synthetic regions with predefined accessibility values
and verifies correct classification.
"""

import sys
import numpy as np
from engine import SimulationConfig, EpigeneticsEngine, ChromatinState


def test_chromatin():
    # Minimal config with zero dt and zero rates to keep state fixed.
    cfg = SimulationConfig(
        random_seed=42,
        time_steps=1,
        dt=1e-9,
        num_regions=3,
        development_mode=False,
        strict_validation=False,
        # Zero out all rates
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
        expression_noise=0.0,  # also zero
    )
    eng = EpigeneticsEngine(cfg)
    eng.initialize_state()

    # Set accessibility directly to known values.
    # We also need to set acetylation and methylation to something,
    # but with rates zero they won't affect accessibility.
    eng.accessibility = np.array([0.1, 0.5, 0.9])
    # Set other variables to avoid side effects (e.g., expression noise)
    eng.acetylation = np.array([0.5, 0.5, 0.5])
    eng.methylation = np.array([0.5, 0.5, 0.5])

    # Call _step to compute chromatin_state based on current accessibility.
    # Because all rates are zero, accessibility remains unchanged.
    eng._step()

    expected = [
        ChromatinState.CLOSED,
        ChromatinState.INTERMEDIATE,
        ChromatinState.OPEN
    ]

    passed = True
    for i, exp in enumerate(expected):
        got = ChromatinState(eng.chromatin_state[i])
        ok = (got == exp)
        if not ok:
            print(f"  Region {i}: acc={eng.accessibility[i]:.2f}, expected {exp.name}, got {got.name}")
            passed = False

    # Check counts sum to num_regions
    counts = {int(v): 0 for v in ChromatinState}
    for state in eng.chromatin_state:
        counts[int(state)] = counts.get(int(state), 0) + 1
    sum_ok = sum(counts.values()) == cfg.num_regions
    if not sum_ok:
        print(f"  Chromatin state counts sum to {sum(counts.values())}, expected {cfg.num_regions}")
        passed = False

    # Determinism: re-run with same config and compare
    eng2 = EpigeneticsEngine(cfg)
    eng2.initialize_state()
    eng2.accessibility = eng.accessibility.copy()
    eng2.acetylation = eng.acetylation.copy()
    eng2.methylation = eng.methylation.copy()
    eng2._step()
    deterministic = np.array_equal(eng.chromatin_state, eng2.chromatin_state)
    if not deterministic:
        print("  Determinism failed")
        passed = False

    print("validate_chromatin")
    print(f"  All chromatin states correctly assigned: {passed}")
    print(f"  Counts sum to num_regions: {sum_ok}")
    print(f"  Deterministic: {deterministic}")
    print(f"  RESULT: {'PASS' if passed else 'FAIL'}")
    return passed


if __name__ == "__main__":
    sys.exit(0 if test_chromatin() else 1)