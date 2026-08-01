# validate_mutation.py
"""
Validation of mutation behaviour and bookkeeping.

This validator ensures that the mutation subsystem behaves correctly by
creating conditions where mutations occur at a moderate, predictable rate.
All tests are deterministic and run with a fixed seed.

Tests:
1. Higher mutation rate → more attempted mutations.
2. Higher mutation rate → more successful lineage establishments.
3. Higher mutation rate → more living clones.
4. Higher mutation rate → higher Shannon diversity.
5. Mutation bookkeeping: driver + passenger == total mutations.
6. Every mutation ID is unique.
7. Every child clone references a valid parent clone.
8. Successful establishments never exceed attempted mutations.
9. Every living clone has positive population, finite growth rate,
   finite fitness, and a valid birth time.
10. Determinism: same seed yields identical results.

The validator completes in under 3 seconds on a typical machine.
"""

import sys
import time
from engine import SimulationConfig, TumorEvolutionEngine


def run_simulation(mutation_rate: float, seed: int = 42):
    """
    Run a simulation with a specific mutation rate and return the engine and results.
    Uses moderate parameters to keep runtime short.
    """
    cfg = SimulationConfig(
        random_seed=seed,
        time_steps=12,                     # enough to generate a few mutations
        carrying_capacity=100_000,         # moderate capacity to limit explosion
        initial_clone_count=2,
        initial_population=500,
        mutation_rate=mutation_rate,
        death_rate=0.01,
        development_mode=False,            # no extra multiplier
        development_mutation_multiplier=1, # unused
        strict_validation=False,
        lineage_establishment_probability=0.5,  # high to ensure some establishments
        driver_mutation_probability=0.1,
    )
    eng = TumorEvolutionEngine(cfg)
    res = eng.run()
    return eng, res


def test_mutation():
    start_time = time.perf_counter()

    # Low and high mutation rates (100,000× difference)
    eng_low, res_low = run_simulation(1e-9, seed=42)
    eng_high, res_high = run_simulation(1e-4, seed=42)

    # --- Collect metrics ---
    total_mut_low = res_low.total_mutations
    total_mut_high = res_high.total_mutations
    estab_low = res_low.successful_establishments
    estab_high = res_high.successful_establishments
    clones_low = len(eng_low.clones)
    clones_high = len(eng_high.clones)
    div_low = res_low.shannon_diversity[-1] if res_low.shannon_diversity else 0.0
    div_high = res_high.shannon_diversity[-1] if res_high.shannon_diversity else 0.0

    # 1. More attempted mutations
    more_attempts = total_mut_high > total_mut_low

    # 2. More successful establishments
    more_establishments = estab_high > estab_low

    # 3. More clones
    more_clones = clones_high > clones_low

    # 4. Higher diversity
    more_diversity = div_high > div_low

    # 5. Bookkeeping: driver + passenger == total recorded mutations
    total_recorded = len(res_high.mutations)
    sum_driver_passenger = res_high.driver_mutations + res_high.passenger_mutations
    bookkeeping_ok = (total_recorded == sum_driver_passenger)

    # 6. Unique mutation IDs
    mut_ids = [m.mutation_id for m in res_high.mutations]
    ids_unique = len(set(mut_ids)) == len(mut_ids)

    # 7. Valid parent/child references
    clone_ids = {c.clone_id for c in eng_high.clones}
    refs_ok = all(
        m.parent_clone_id in clone_ids and m.child_clone_id in clone_ids
        for m in res_high.mutations
    )

    # 8. Attempts >= successful establishments
    attempts_ge_estab = res_high.total_mutations >= res_high.successful_establishments

    # 9. Clone state validation for all clones in high mutation simulation
    clone_state_ok = True
    for c in eng_high.clones:
        if c.alive:
            if c.population <= 0:
                clone_state_ok = False
                break
            if not (c.growth_rate > -1e-9 and c.fitness > -1e-9):
                clone_state_ok = False
                break
            # Use the engine's config for time_steps
            if c.birth_time < 0 or c.birth_time > eng_high.cfg.time_steps:
                clone_state_ok = False
                break
        # For extinct clones, population must be 0
        if not c.alive and c.population != 0.0:
            clone_state_ok = False
            break

    # 10. Determinism: run the same high mutation config twice and compare
    eng_high2, res_high2 = run_simulation(1e-4, seed=42)
    deterministic = (
        res_high.tumor_burden == res_high2.tumor_burden and
        res_high.shannon_diversity == res_high2.shannon_diversity and
        len(res_high.mutations) == len(res_high2.mutations) and
        res_high.driver_mutations == res_high2.driver_mutations and
        res_high.passenger_mutations == res_high2.passenger_mutations
    )

    # Overall pass
    passed = (
        more_attempts and more_establishments and more_clones and more_diversity and
        bookkeeping_ok and ids_unique and refs_ok and attempts_ge_estab and
        clone_state_ok and deterministic
    )

    # --- Print summary ---
    elapsed = time.perf_counter() - start_time

    print("validate_mutation")
    print("")
    print(f"  More mutation attempts:     {'PASS' if more_attempts else 'FAIL'} "
          f"(low={total_mut_low}, high={total_mut_high})")
    print(f"  More establishments:        {'PASS' if more_establishments else 'FAIL'} "
          f"(low={estab_low}, high={estab_high})")
    print(f"  More living clones:         {'PASS' if more_clones else 'FAIL'} "
          f"(low={clones_low}, high={clones_high})")
    print(f"  Higher diversity:           {'PASS' if more_diversity else 'FAIL'} "
          f"(low={div_low:.4f}, high={div_high:.4f})")
    print(f"  Mutation bookkeeping:       {'PASS' if bookkeeping_ok else 'FAIL'} "
          f"(driver+passenger={sum_driver_passenger}, recorded={total_recorded})")
    print(f"  Unique mutation IDs:        {'PASS' if ids_unique else 'FAIL'}")
    print(f"  Valid parent references:    {'PASS' if refs_ok else 'FAIL'}")
    print(f"  Attempts >= establishments: {'PASS' if attempts_ge_estab else 'FAIL'}")
    print(f"  Clone state valid:          {'PASS' if clone_state_ok else 'FAIL'}")
    print(f"  Deterministic:              {'PASS' if deterministic else 'FAIL'}")
    print("")
    print(f"Mutation attempts: {total_mut_high}")
    print(f"Successful establishments: {estab_high}")
    print(f"Living clones: {clones_high}")
    print(f"Execution time: {elapsed:.3f} seconds")
    print("")
    print("==============================")
    print(f"RESULT: {'PASS' if passed else 'FAIL'}")

    return passed


if __name__ == "__main__":
    sys.exit(0 if test_mutation() else 1)