# validate_growth.py
"""
Validation of logistic growth dynamics under the birth-death model.

Tests:
- Population increases from a small initial tumour.
- Growth slows as carrying capacity is approached.
- Population never exceeds carrying capacity (within numerical tolerance).
- Population never becomes negative.
- No NaN or infinite values.
- Numerical stability over time.
"""

import sys
import math
from engine import SimulationConfig, TumorEvolutionEngine


def test_growth():
    # Isolate logistic growth: no death, no mutations, single clone.
    cfg = SimulationConfig(
        random_seed=42,
        time_steps=40,                  # sufficient to approach K
        carrying_capacity=1_000_000,
        initial_clone_count=1,
        initial_population=1000,
        mutation_rate=0.0,
        death_rate=0.0,                 # no death
        development_mode=False,
        strict_validation=False,        # avoid overhead for this test
    )
    eng = TumorEvolutionEngine(cfg)
    res = eng.run()

    burden = res.tumor_burden
    K = cfg.carrying_capacity

    # 1. Monotonic increase (allow tiny floating errors)
    monotonic = all(burden[i] <= burden[i+1] + 1e-9 for i in range(len(burden)-1))

    # 2. Never exceeds K (with tolerance)
    never_exceeds = all(b <= K + 1e-6 for b in burden)

    # 3. Growth slows: compare first and last differences
    diffs = [burden[i+1] - burden[i] for i in range(len(burden)-1)]
    slows = diffs[-1] < diffs[0] if len(diffs) > 1 else True

    # 4. Non‑negative and finite
    non_negative = all(b >= 0 for b in burden)
    finite = all(math.isfinite(b) for b in burden)

    # 5. No NaN / Inf in clone populations (checked via finite)
    # 6. Carrying capacity constrains growth: final burden within 10% of K (stochastic)
    final = burden[-1]
    approaches = abs(final - K) <= 0.10 * K   # 10% tolerance due to stochasticity

    passed = (monotonic and never_exceeds and slows and non_negative and finite and approaches)

    print("validate_growth:")
    print(f"  Monotonic increase: {monotonic}")
    print(f"  Never exceeds K: {never_exceeds}")
    print(f"  Growth slows: {slows}")
    print(f"  Non-negative: {non_negative}")
    print(f"  Finite values: {finite}")
    print(f"  Approaches K (within 10%): {approaches} (final={final:.2f}, K={K})")
    print(f"  RESULT: {'PASS' if passed else 'FAIL'}")
    return passed


if __name__ == "__main__":
    sys.exit(0 if test_growth() else 1)