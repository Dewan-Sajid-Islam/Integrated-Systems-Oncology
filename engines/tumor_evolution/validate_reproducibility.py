# validate_reproducibility.py
"""
Validation of deterministic reproducibility.

Tests:
- Same random seed produces identical results across all recorded fields.
- Different random seeds produce different results.
"""

import sys
from engine import SimulationConfig, TumorEvolutionEngine


def compare_results(res1, res2, label):
    """Compare two SimulationResults objects; return True if all relevant fields match."""
    match = True
    if res1.tumor_burden != res2.tumor_burden:
        print(f"  {label}: tumor_burden differs")
        match = False
    if res1.shannon_diversity != res2.shannon_diversity:
        print(f"  {label}: shannon_diversity differs")
        match = False
    if res1.simpson_diversity != res2.simpson_diversity:
        print(f"  {label}: simpson_diversity differs")
        match = False
    if res1.mutation_events != res2.mutation_events:
        print(f"  {label}: mutation_events differ")
        match = False
    if len(res1.mutations) != len(res2.mutations):
        print(f"  {label}: mutation count differs")
        match = False
    else:
        for m1, m2 in zip(res1.mutations, res2.mutations):
            if (m1.mutation_id != m2.mutation_id or
                m1.mutation_type != m2.mutation_type or
                m1.affected_traits != m2.affected_traits):
                print(f"  {label}: mutation content differs")
                match = False
                break
    if res1.clone_frequencies != res2.clone_frequencies:
        print(f"  {label}: clone_frequencies differ")
        match = False
    if res1.clone_populations != res2.clone_populations:
        print(f"  {label}: clone_populations differ")
        match = False
    if res1.clone_fitness != res2.clone_fitness:
        print(f"  {label}: clone_fitness differ")
        match = False
    if res1.extinction_times != res2.extinction_times:
        print(f"  {label}: extinction_times differ")
        match = False
    # Also check summary statistics
    if res1.driver_mutations != res2.driver_mutations:
        print(f"  {label}: driver_mutations differ")
        match = False
    if res1.passenger_mutations != res2.passenger_mutations:
        print(f"  {label}: passenger_mutations differ")
        match = False
    return match


def test_reproducibility():
    cfg = SimulationConfig(
        random_seed=42,
        time_steps=8,
        carrying_capacity=1_000_000,
        initial_clone_count=2,
        initial_population=500,
        mutation_rate=1e-5,
        death_rate=0.01,
        development_mode=False,
        strict_validation=False,
        lineage_establishment_probability=0.3,
    )

    # Same seed twice
    eng1 = TumorEvolutionEngine(cfg)
    res1 = eng1.run()
    eng2 = TumorEvolutionEngine(cfg)
    res2 = eng2.run()
    same_seed_match = compare_results(res1, res2, "Same seed")

    # Different seed
    cfg2 = SimulationConfig(**cfg.__dict__)
    cfg2.random_seed = 123
    eng3 = TumorEvolutionEngine(cfg2)
    res3 = eng3.run()
    # Check that results differ (at least some difference)
    diff_seed_diff = (res1.tumor_burden != res3.tumor_burden or
                      len(res1.mutations) != len(res3.mutations) or
                      res1.clone_frequencies != res3.clone_frequencies)

    passed = same_seed_match and diff_seed_diff
    print("validate_reproducibility:")
    print(f"  Same seed: results identical? {same_seed_match}")
    print(f"  Different seed: results differ? {diff_seed_diff}")
    print(f"  RESULT: {'PASS' if passed else 'FAIL'}")
    return passed


if __name__ == "__main__":
    sys.exit(0 if test_reproducibility() else 1)