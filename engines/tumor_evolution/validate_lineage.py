# validate_lineage.py
"""
Validation of lineage tracking and tree integrity.

Tests:
- Unique clone IDs.
- Parent ID validity (exists or None for roots).
- Generation number equals parent generation + 1.
- Root ancestor consistent within a lineage.
- No cycles in the lineage graph.
- Mutation objects reference existing clones.
- Lineage depth in Mutation objects equals clone generation.
- Alive/extinct clones are correctly marked.
"""

import sys
from engine import SimulationConfig, TumorEvolutionEngine


def test_lineage():
    # Run a simulation with mutations to build a lineage tree
    cfg = SimulationConfig(
        random_seed=42,
        time_steps=15,
        carrying_capacity=1_000_000,
        initial_clone_count=2,
        initial_population=500,
        mutation_rate=1e-5,
        death_rate=0.01,
        development_mode=False,
        strict_validation=False,
        lineage_establishment_probability=0.3,
    )
    eng = TumorEvolutionEngine(cfg)
    res = eng.run()

    clone_ids = {c.clone_id for c in eng.clones}
    passed = True

    # 1. Unique IDs (set size equals list length)
    if len(clone_ids) != len(eng.clones):
        print("  Duplicate clone IDs detected")
        passed = False

    # 2. Parent validity, generation, root ancestor
    for c in eng.clones:
        if c.parent_id is None:
            if c.generation != 0:
                print(f"  Root clone {c.clone_id} has generation {c.generation} != 0")
                passed = False
            if c.root_ancestor != c.clone_id:
                print(f"  Root clone {c.clone_id} root_ancestor mismatch")
                passed = False
        else:
            if c.parent_id not in clone_ids:
                print(f"  Clone {c.clone_id} has invalid parent {c.parent_id}")
                passed = False
            parent = next((p for p in eng.clones if p.clone_id == c.parent_id), None)
            if parent:
                if c.generation != parent.generation + 1:
                    print(f"  Clone {c.clone_id} generation {c.generation} != parent+1")
                    passed = False
                if c.root_ancestor != parent.root_ancestor:
                    print(f"  Clone {c.clone_id} root_ancestor mismatch with parent")
                    passed = False

    # 3. No cycles (manual check)
    visited = set()
    for clone in eng.clones:
        if clone.clone_id in visited:
            continue
        current = clone
        chain = set()
        while current is not None:
            if current.clone_id in chain:
                print(f"  Cycle detected involving clone {current.clone_id}")
                passed = False
                break
            chain.add(current.clone_id)
            if current.parent_id is None:
                break
            current = next((c for c in eng.clones if c.clone_id == current.parent_id), None)
        visited.update(chain)

    # 4. Mutation references and lineage depth
    for mut in res.mutations:
        if mut.parent_clone_id not in clone_ids:
            print(f"  Mutation {mut.mutation_id} invalid parent")
            passed = False
        if mut.child_clone_id not in clone_ids:
            print(f"  Mutation {mut.mutation_id} invalid child")
            passed = False
        child = next((c for c in eng.clones if c.clone_id == mut.child_clone_id), None)
        if child:
            if mut.lineage_depth != child.generation:
                print(f"  Mutation {mut.mutation_id} lineage_depth {mut.lineage_depth} != clone generation {child.generation}")
                passed = False

    # 5. Alive/Extinct consistency: extinct clones have population 0 and are not alive
    for c in eng.clones:
        if not c.alive and c.population != 0.0:
            print(f"  Extinct clone {c.clone_id} has non-zero population")
            passed = False
        if c.alive and c.population < 0:
            print(f"  Alive clone {c.clone_id} has negative population")
            passed = False

    print("validate_lineage:")
    print(f"  Lineage integrity: {'PASS' if passed else 'FAIL'}")
    print(f"  RESULT: {'PASS' if passed else 'FAIL'}")
    return passed


if __name__ == "__main__":
    sys.exit(0 if test_lineage() else 1)