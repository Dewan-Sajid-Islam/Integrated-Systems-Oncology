# validate_diversity.py
"""
Validation of Shannon and Simpson diversity indices against analytical calculations.

Tests are performed by constructing known clone population distributions
and comparing engine results to exact values.

Edge cases: single clone, equal clones, dominant clone, empty tumour.
"""

import sys
import math
from engine import SimulationConfig, TumorEvolutionEngine, Clone


def run_diversity_test(populations):
    """
    Create a fresh engine, initialize it, then manually set clone populations
    according to the provided list. Returns (shannon, simpson).
    """
    # We need a config to create an engine; we'll use a minimal one.
    cfg = SimulationConfig(
        random_seed=42,
        time_steps=1,
        initial_clone_count=len(populations),
        initial_population=1,          # will be overridden
        mutation_rate=0.0,
        death_rate=0.0,
        development_mode=False,
        strict_validation=False,
    )
    eng = TumorEvolutionEngine(cfg)
    eng.initialize_population()   # creates clones with population=1 each

    # Override populations and alive status
    for i, pop in enumerate(populations):
        if i < len(eng.clones):
            c = eng.clones[i]
            c.population = pop
            if pop <= 0:
                c.alive = False
                c.population = 0.0
            else:
                c.alive = True
            # Update rates (birth/death) to compute fitness (not needed for diversity)
            eng._update_clone_rates(c)

    # If there are more clones than provided, mark extras extinct
    for i in range(len(populations), len(eng.clones)):
        eng.clones[i].alive = False
        eng.clones[i].population = 0.0

    return eng.shannon(), eng.simpson()


def test_diversity():
    test_cases = [
        ([100], 0.0, 0.0),
        ([100, 100], math.log(2), 0.5),
        ([100, 100, 100], math.log(3), 2/3),
        ([100, 100, 100, 100], math.log(4), 0.75),
        ([900, 100], - (0.9*math.log(0.9) + 0.1*math.log(0.1)), 1 - (0.81 + 0.01)),
        ([0], 0.0, 0.0),   # empty tumour
    ]

    passed_all = True
    for i, (pops, exp_shannon, exp_simpson) in enumerate(test_cases):
        comp_shannon, comp_simpson = run_diversity_test(pops)
        tol = 1e-9
        shannon_ok = math.isclose(comp_shannon, exp_shannon, rel_tol=tol, abs_tol=tol)
        simpson_ok = math.isclose(comp_simpson, exp_simpson, rel_tol=tol, abs_tol=tol)
        case_ok = shannon_ok and simpson_ok
        if not case_ok:
            passed_all = False
        print(f"  Case {i+1}: pops={pops}")
        print(f"    Shannon: expected={exp_shannon:.6f}, computed={comp_shannon:.6f} -> {'OK' if shannon_ok else 'FAIL'}")
        print(f"    Simpson: expected={exp_simpson:.6f}, computed={comp_simpson:.6f} -> {'OK' if simpson_ok else 'FAIL'}")

    print("validate_diversity:")
    print(f"  RESULT: {'PASS' if passed_all else 'FAIL'}")
    return passed_all


if __name__ == "__main__":
    sys.exit(0 if test_diversity() else 1)