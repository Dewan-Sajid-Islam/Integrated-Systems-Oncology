from __future__ import annotations
from dataclasses import dataclass, field
from typing import Optional, List, Dict, Tuple, Set, Callable
import math
import numpy as np

ENGINE_VERSION = "0.5.0"


@dataclass
class SimulationConfig:
    """Configuration parameters for the tumor evolution simulation."""

    # Core simulation parameters
    random_seed: int = 42
    time_steps: int = 10
    carrying_capacity: float = 1_000_000.0
    initial_clone_count: int = 3
    initial_population: float = 1000.0

    # Mutation parameters
    mutation_rate: float = 1e-6
    development_mode: bool = True
    development_mutation_multiplier: float = 150.0
    lineage_establishment_probability: float = 0.05
    driver_mutation_probability: float = 0.1
    driver_effect_scale: float = 0.1       # scale for driver effects on phenotype traits
    passenger_effect_scale: float = 0.01   # scale for passenger effects on phenotype traits

    # Legacy growth rate (net growth) – will be computed from birth and death
    default_growth_rate: float = 0.35
    death_rate: float = 0.01               # base death rate (per time step)

    # Phenotype base values
    proliferation_base: float = 1.0        # multiplier for birth rate
    apoptosis_base: float = 1.0            # multiplier for death rate
    dna_repair_base: float = 1.0           # affects mutation rate (higher = lower mutation)
    genomic_instability_base: float = 0.0  # increases mutation rate
    metabolic_efficiency_base: float = 1.0 # multiplier for birth (nutrient use)
    immune_visibility_base: float = 0.0    # increases death rate (immune attack)
    epigenetic_plasticity_base: float = 0.0  # affects adaptability (future)
    resistance_base: float = 0.0           # resistance to therapy (future)

    # Derived birth rate base (computed from default_growth_rate and death_rate)
    # This ensures initial net growth equals default_growth_rate
    @property
    def birth_rate_base(self) -> float:
        return self.default_growth_rate + self.death_rate

    # Validation strictness
    strict_validation: bool = True
    extinction_threshold: float = 1e-6


@dataclass
class Mutation:
    """Explicit representation of a mutation event."""
    mutation_id: int
    parent_clone_id: int
    child_clone_id: int
    mutation_type: str                 # "driver" or "passenger"
    time: int
    affected_traits: List[str] = field(default_factory=list)   # which phenotype traits were changed
    fitness_effect: float = 0.0        # change in net fitness (birth - death) due to mutation
    population_at_birth: float = 0.0   # population of the child clone at creation
    lineage_depth: int = 0             # generation number of the child clone


@dataclass
class Clone:
    """Represents a single clone in the tumor population."""
    clone_id: int
    parent_id: Optional[int]
    birth_time: int
    population: float
    mutation_rate: float

    # Intrinsic growth-related parameters (can be modified by mutations)
    proliferation_capacity: float = 1.0     # multiplier for birth rate
    apoptosis_susceptibility: float = 1.0   # multiplier for death rate
    dna_repair_efficiency: float = 1.0      # affects mutation rate (higher = lower mutation)
    genomic_instability: float = 0.0        # increases mutation rate
    metabolic_efficiency: float = 1.0       # multiplier for birth rate
    immune_visibility: float = 0.0          # increases death rate
    epigenetic_plasticity: float = 0.0      # (future) affects adaptability
    resistance_potential: float = 0.0       # (future) resistance to therapy

    # Derived quantities (updated each time step)
    growth_rate: float = 0.0               # net growth = effective_birth - effective_death
    fitness: float = 0.0                   # same as growth_rate (observable quantity)
    new_cells: float = 0.0                 # number of births in the last step

    # Lineage tracking
    alive: bool = True
    age: int = 0
    generation: int = 0                   # depth from root (0 for root)
    root_ancestor: Optional[int] = None   # ID of the original clone this lineage descends from

    # Mutation counts
    driver_mutation_count: int = 0
    passenger_mutation_count: int = 0

    # For validation and statistics
    _last_births: float = 0.0
    _last_deaths: float = 0.0


@dataclass
class SimulationResults:
    """Container for all recorded simulation data."""
    time: List[int] = field(default_factory=list)
    tumor_burden: List[float] = field(default_factory=list)
    shannon_diversity: List[float] = field(default_factory=list)
    mutation_events: List[str] = field(default_factory=list)   # legacy text log
    simpson_diversity: List[float] = field(default_factory=list)
    clone_populations: List[List[Tuple[int, float]]] = field(default_factory=list)
    clone_frequencies: List[Dict[int, float]] = field(default_factory=list)
    mutations: List[Mutation] = field(default_factory=list)    # structured mutation records
    clone_fitness: List[Dict[int, float]] = field(default_factory=list)
    total_mutations: int = 0
    driver_mutations: int = 0
    passenger_mutations: int = 0
    successful_establishments: int = 0
    failed_establishments: int = 0
    extinction_times: Dict[int, int] = field(default_factory=dict)
    extinct_clones: List[int] = field(default_factory=list)


class TumorEvolutionEngine:
    """
    Tumor Evolution Engine for the Integrated Systems Oncology framework.

    This engine models the evolutionary dynamics of a tumour cell population
    using a mechanistic birth–death–mutation process with density-dependent competition.
    Fitness emerges from the balance between intrinsic birth and death rates,
    which are influenced by heritable phenotype traits. Environmental modifiers
    are exposed through hook methods for future integration with metabolism,
    immunity, and therapy engines.

    Version 0.5.0 redesigns the core dynamics to be entirely process-based:
      - Separate birth, death, and mutation processes.
      - Fitness is an observable quantity, not a preset parameter.
      - Expanded phenotype with multiple independent traits.
      - Driver mutations affect phenotype traits, not just growth rate.
      - Lineage tracking includes generation and root ancestor.
      - Validation covers all new fields and invariants.

    All public methods remain available for backwards compatibility.
    """

    def __init__(self, cfg: SimulationConfig):
        self.cfg = cfg
        self.rng = np.random.default_rng(cfg.random_seed)
        self.clones: List[Clone] = []
        self.results = SimulationResults()
        self.next_id = 0
        self._mutation_id_counter = 0
        self._current_time = 0
        self._validate_config()

    # ----------------------------------------------------------------------
    # Configuration validation
    # ----------------------------------------------------------------------

    def _validate_config(self) -> None:
        if self.cfg.carrying_capacity <= 0:
            raise ValueError("carrying_capacity must be positive")
        if not (0 <= self.cfg.death_rate <= 1):
            raise ValueError("death_rate must be between 0 and 1")
        if self.cfg.initial_population < 0:
            raise ValueError("initial_population must be non-negative")
        if self.cfg.initial_clone_count < 1:
            raise ValueError("initial_clone_count must be at least 1")
        if self.cfg.mutation_rate < 0:
            raise ValueError("mutation_rate must be non-negative")
        if self.cfg.default_growth_rate < 0:
            raise ValueError("default_growth_rate must be non-negative")
        if not (0 <= self.cfg.driver_mutation_probability <= 1):
            raise ValueError("driver_mutation_probability must be between 0 and 1")
        if self.cfg.driver_effect_scale < 0:
            raise ValueError("driver_effect_scale must be non-negative")
        if self.cfg.passenger_effect_scale < 0:
            raise ValueError("passenger_effect_scale must be non-negative")
        if self.cfg.proliferation_base <= 0:
            raise ValueError("proliferation_base must be positive")
        if self.cfg.apoptosis_base <= 0:
            raise ValueError("apoptosis_base must be positive")
        if self.cfg.dna_repair_base <= 0:
            raise ValueError("dna_repair_base must be positive")
        if self.cfg.metabolic_efficiency_base <= 0:
            raise ValueError("metabolic_efficiency_base must be positive")
        if self.cfg.immune_visibility_base < 0:
            raise ValueError("immune_visibility_base must be non-negative")
        if self.cfg.genomic_instability_base < 0:
            raise ValueError("genomic_instability_base must be non-negative")

    # ----------------------------------------------------------------------
    # Population initialisation
    # ----------------------------------------------------------------------

    def initialize_population(self) -> None:
        """Create the initial set of clones with default phenotype and rates."""
        self.clones = []
        self.next_id = 0
        self._mutation_id_counter = 0
        self.results = SimulationResults()

        for _ in range(self.cfg.initial_clone_count):
            clone = Clone(
                clone_id=self.next_id,
                parent_id=None,
                birth_time=0,
                population=self.cfg.initial_population,
                mutation_rate=self.cfg.mutation_rate,
                proliferation_capacity=self.cfg.proliferation_base,
                apoptosis_susceptibility=self.cfg.apoptosis_base,
                dna_repair_efficiency=self.cfg.dna_repair_base,
                genomic_instability=self.cfg.genomic_instability_base,
                metabolic_efficiency=self.cfg.metabolic_efficiency_base,
                immune_visibility=self.cfg.immune_visibility_base,
                epigenetic_plasticity=self.cfg.epigenetic_plasticity_base,
                resistance_potential=self.cfg.resistance_base,
                generation=0,
                root_ancestor=self.next_id,
            )
            # Compute initial growth rate and fitness
            self._update_clone_rates(clone)
            self.clones.append(clone)
            self.next_id += 1

    # ----------------------------------------------------------------------
    # Rate computation and environmental hooks
    # ----------------------------------------------------------------------

    def effective_birth_rate(self, clone: Clone) -> float:
        """
        Compute the effective birth rate for a clone.

        The birth rate is influenced by:
          - Intrinsic proliferation capacity
          - Metabolic efficiency
          - Density dependence (competition for resources)
        Future engines can modify this via overrides.
        """
        # Base birth rate from configuration
        base = self.cfg.birth_rate_base
        # Intrinsic modifiers
        intrinsic = clone.proliferation_capacity * clone.metabolic_efficiency
        # Density dependence (competition)
        total_pop = sum(c.population for c in self.clones if c.alive)
        density_factor = max(0.0, 1.0 - total_pop / self.cfg.carrying_capacity)
        # Combine
        return base * intrinsic * density_factor

    def effective_death_rate(self, clone: Clone) -> float:
        """
        Compute the effective death rate for a clone.

        The death rate is influenced by:
          - Intrinsic apoptosis susceptibility
          - Immune visibility (increases death)
        Future engines can modify this via overrides.
        """
        base = self.cfg.death_rate
        intrinsic = clone.apoptosis_susceptibility * (1.0 + clone.immune_visibility)
        # No density dependence on death (but could be added)
        return base * intrinsic

    def effective_mutation_rate(self, clone: Clone) -> float:
        """
        Compute the effective mutation rate per cell division.

        Influenced by:
          - Base mutation rate
          - DNA repair efficiency (inverse)
          - Genomic instability (additive)
        Future engines can modify this via overrides.
        """
        base = self.cfg.mutation_rate
        repair_factor = 1.0 / max(0.1, clone.dna_repair_efficiency)
        instability_factor = 1.0 + clone.genomic_instability
        return base * repair_factor * instability_factor

    def _update_clone_rates(self, clone: Clone) -> None:
        """Update the derived rates (growth_rate and fitness) from current phenotype."""
        birth = self.effective_birth_rate(clone)
        death = self.effective_death_rate(clone)
        clone.growth_rate = birth - death
        clone.fitness = clone.growth_rate   # fitness is an observable quantity

    # ----------------------------------------------------------------------
    # Diversity and frequency helpers
    # ----------------------------------------------------------------------

    def shannon(self) -> float:
        total = sum(c.population for c in self.clones if c.alive)
        if total <= 0:
            return 0.0
        h = 0.0
        for c in self.clones:
            if not c.alive or c.population <= 0:
                continue
            p = c.population / total
            h -= p * math.log(p)
        return h

    def simpson(self) -> float:
        total = sum(c.population for c in self.clones if c.alive)
        if total <= 0:
            return 0.0
        sum_sq = sum((c.population / total) ** 2 for c in self.clones if c.alive and c.population > 0)
        return 1.0 - sum_sq

    def get_clone_frequencies(self) -> Dict[int, float]:
        total = sum(c.population for c in self.clones if c.alive)
        if total <= 0:
            return {c.clone_id: 0.0 for c in self.clones if c.alive}
        return {c.clone_id: c.population / total for c in self.clones if c.alive}

    # ----------------------------------------------------------------------
    # Recording
    # ----------------------------------------------------------------------

    def record(self, t: int) -> None:
        alive_clones = [c for c in self.clones if c.alive]
        total = sum(c.population for c in alive_clones)
        self.results.time.append(t)
        self.results.tumor_burden.append(total)
        self.results.shannon_diversity.append(self.shannon())
        self.results.simpson_diversity.append(self.simpson())

        snapshot = [(c.clone_id, c.population) for c in alive_clones if c.population > 0]
        self.results.clone_populations.append(snapshot)
        self.results.clone_frequencies.append(self.get_clone_frequencies())

        fitness_dict = {c.clone_id: c.fitness for c in alive_clones}
        self.results.clone_fitness.append(fitness_dict)

        if self.cfg.strict_validation:
            self.validate_state()

    # ----------------------------------------------------------------------
    # Biological processes
    # ----------------------------------------------------------------------

    def growth(self) -> None:
        """
        Birth process: each clone produces offspring according to its effective birth rate.
        New cells are added to the clone's population.
        The number of births is drawn from a Poisson distribution.
        """
        for c in self.clones:
            if not c.alive:
                continue
            birth_rate = self.effective_birth_rate(c)
            # Expectation: birth_rate * population (per time step)
            expected_births = birth_rate * c.population
            births = self.rng.poisson(expected_births)
            c.population += births
            c.new_cells = births
            c._last_births = births
            self._update_clone_rates(c)

    def mutate(self, t: int) -> None:
        """
        Mutation process: mutations occur during cell division.
        The expected number of mutation events is proportional to the number of births
        and the effective mutation rate.
        Each mutation event may create a new clone if it successfully establishes.
        """
        est_prob = self.cfg.lineage_establishment_probability
        if self.cfg.development_mode:
            est_prob = 0.3  # higher visibility for testing

        mult = self.cfg.development_mutation_multiplier if self.cfg.development_mode else 1.0
        new_clones = []
        alive_parents = [c for c in self.clones if c.alive]

        attempts_total = 0
        established_drivers = 0
        established_passengers = 0

        for parent in alive_parents:
            # Expected mutations based on births in this step
            expected = parent.new_cells * self.effective_mutation_rate(parent) * mult
            attempts = self.rng.poisson(expected)
            attempts_total += attempts

            for _ in range(attempts):
                # Determine mutation type
                if self.rng.random() < self.cfg.driver_mutation_probability:
                    mut_type = "driver"
                    effect_scale = self.cfg.driver_effect_scale
                else:
                    mut_type = "passenger"
                    effect_scale = self.cfg.passenger_effect_scale

                # Lineage establishment
                if self.rng.random() > est_prob:
                    continue

                # Seed population taken from parent
                seed = max(1.0, parent.population * 0.005)
                parent.population -= seed
                if parent.population < 0:
                    parent.population = 0.0

                # Create child clone with inherited phenotype
                child = Clone(
                    clone_id=self.next_id,
                    parent_id=parent.clone_id,
                    birth_time=t,
                    population=seed,
                    mutation_rate=parent.mutation_rate,
                    proliferation_capacity=parent.proliferation_capacity,
                    apoptosis_susceptibility=parent.apoptosis_susceptibility,
                    dna_repair_efficiency=parent.dna_repair_efficiency,
                    genomic_instability=parent.genomic_instability,
                    metabolic_efficiency=parent.metabolic_efficiency,
                    immune_visibility=parent.immune_visibility,
                    epigenetic_plasticity=parent.epigenetic_plasticity,
                    resistance_potential=parent.resistance_potential,
                    generation=parent.generation + 1,
                    root_ancestor=parent.root_ancestor or parent.clone_id,
                )

                # Apply phenotype mutation
                affected = self._apply_phenotype_mutation(child, mut_type, effect_scale)

                # Update counts
                if mut_type == "driver":
                    child.driver_mutation_count = parent.driver_mutation_count + 1
                    established_drivers += 1
                else:
                    child.passenger_mutation_count = parent.passenger_mutation_count + 1
                    established_passengers += 1

                # Compute rates for child
                self._update_clone_rates(child)

                # Record mutation
                parent_fitness = parent.fitness
                mutation = Mutation(
                    mutation_id=self._mutation_id_counter,
                    parent_clone_id=parent.clone_id,
                    child_clone_id=child.clone_id,
                    mutation_type=mut_type,
                    time=t,
                    affected_traits=affected,
                    fitness_effect=child.fitness - parent_fitness,
                    population_at_birth=seed,
                    lineage_depth=child.generation,
                )
                self.results.mutations.append(mutation)
                self._mutation_id_counter += 1
                self.results.mutation_events.append(
                    f"t={t}: {parent.clone_id}->{child.clone_id} ({mut_type})"
                )

                new_clones.append(child)
                self.next_id += 1

        self.clones.extend(new_clones)

        # Update statistics
        self.results.total_mutations += attempts_total
        self.results.driver_mutations += established_drivers
        self.results.passenger_mutations += established_passengers
        self.results.successful_establishments += len(new_clones)
        self.results.failed_establishments += (attempts_total - len(new_clones))

    def _apply_phenotype_mutation(self, clone: Clone, mut_type: str, effect_scale: float) -> List[str]:
        """
        Apply a mutation effect to one or more phenotype traits.
        Returns a list of affected trait names.
        """
        affected = []
        # Number of traits affected: for drivers, possibly 1-2; for passengers, usually 1
        n_traits = self.rng.integers(1, 3) if mut_type == "driver" else 1

        # Possible traits
        trait_names = [
            "proliferation_capacity",
            "apoptosis_susceptibility",
            "dna_repair_efficiency",
            "genomic_instability",
            "metabolic_efficiency",
            "immune_visibility",
            "epigenetic_plasticity",
            "resistance_potential",
        ]
        # Choose traits without replacement
        chosen = self.rng.choice(len(trait_names), size=n_traits, replace=False)
        for idx in chosen:
            trait = trait_names[idx]
            effect = self.rng.normal(0, effect_scale)
            if trait == "proliferation_capacity":
                clone.proliferation_capacity = max(0.1, clone.proliferation_capacity + effect)
            elif trait == "apoptosis_susceptibility":
                clone.apoptosis_susceptibility = max(0.1, clone.apoptosis_susceptibility + effect)
            elif trait == "dna_repair_efficiency":
                clone.dna_repair_efficiency = max(0.1, clone.dna_repair_efficiency + effect)
            elif trait == "genomic_instability":
                clone.genomic_instability = max(0.0, clone.genomic_instability + effect)
            elif trait == "metabolic_efficiency":
                clone.metabolic_efficiency = max(0.1, clone.metabolic_efficiency + effect)
            elif trait == "immune_visibility":
                clone.immune_visibility = max(0.0, clone.immune_visibility + effect)
            elif trait == "epigenetic_plasticity":
                clone.epigenetic_plasticity = max(0.0, clone.epigenetic_plasticity + effect)
            elif trait == "resistance_potential":
                clone.resistance_potential = max(0.0, clone.resistance_potential + effect)
            affected.append(trait)
        return affected

    def death(self) -> None:
        """
        Death process: cells die according to the clone's effective death rate.
        The number of deaths is drawn from a Poisson distribution.
        Clones whose population falls below the extinction threshold are marked extinct.
        """
        for c in self.clones:
            if not c.alive:
                continue
            death_rate = self.effective_death_rate(c)
            expected_deaths = death_rate * c.population
            deaths = self.rng.poisson(expected_deaths)
            c.population -= deaths
            c._last_deaths = deaths
            if c.population < 0:
                c.population = 0.0

            # Extinction
            if c.population < self.cfg.extinction_threshold:
                if c.alive:  # prevent duplicate
                    self.results.extinction_times[c.clone_id] = self._current_time
                    self.results.extinct_clones.append(c.clone_id)
                c.alive = False
                c.population = 0.0

            # Update rates (death changes might affect fitness)
            self._update_clone_rates(c)

    def selection(self) -> None:
        """
        Legacy method: now selection emerges naturally from birth and death rates.
        This method is kept for backwards compatibility but does nothing.
        """
        pass

    # ----------------------------------------------------------------------
    # Validation
    # ----------------------------------------------------------------------

    def validate_state(self) -> None:
        """Perform extensive internal consistency checks."""
        # No duplicate clone IDs
        ids = [c.clone_id for c in self.clones]
        if len(set(ids)) != len(ids):
            raise RuntimeError("Duplicate clone IDs detected")

        # Mutation IDs unique
        mut_ids = [m.mutation_id for m in self.results.mutations]
        if len(set(mut_ids)) != len(mut_ids):
            raise RuntimeError("Duplicate mutation IDs detected")

        # Populations and rates valid
        for c in self.clones:
            if c.alive:
                if c.population < 0:
                    raise RuntimeError(f"Clone {c.clone_id} negative population {c.population}")
                if math.isnan(c.population) or math.isinf(c.population):
                    raise RuntimeError(f"Clone {c.clone_id} invalid population")
                if c.growth_rate < -1e-9 or math.isnan(c.growth_rate):
                    raise RuntimeError(f"Clone {c.clone_id} invalid growth rate {c.growth_rate}")
                if c.fitness < -1e-9 or math.isnan(c.fitness):
                    raise RuntimeError(f"Clone {c.clone_id} invalid fitness {c.fitness}")
                # Phenotype bounds
                if c.proliferation_capacity <= 0:
                    raise RuntimeError(f"Clone {c.clone_id} non-positive proliferation_capacity")
                if c.apoptosis_susceptibility <= 0:
                    raise RuntimeError(f"Clone {c.clone_id} non-positive apoptosis_susceptibility")
                if c.dna_repair_efficiency <= 0:
                    raise RuntimeError(f"Clone {c.clone_id} non-positive dna_repair_efficiency")
                if c.genomic_instability < 0:
                    raise RuntimeError(f"Clone {c.clone_id} negative genomic_instability")
                if c.metabolic_efficiency <= 0:
                    raise RuntimeError(f"Clone {c.clone_id} non-positive metabolic_efficiency")
                if c.immune_visibility < 0:
                    raise RuntimeError(f"Clone {c.clone_id} negative immune_visibility")
                if c.epigenetic_plasticity < 0:
                    raise RuntimeError(f"Clone {c.clone_id} negative epigenetic_plasticity")
                if c.resistance_potential < 0:
                    raise RuntimeError(f"Clone {c.clone_id} negative resistance_potential")
            else:
                if c.population != 0.0:
                    raise RuntimeError(f"Extinct clone {c.clone_id} has non-zero population")

        # Parent IDs must exist
        clone_ids = {c.clone_id for c in self.clones}
        for c in self.clones:
            if c.parent_id is not None and c.parent_id not in clone_ids:
                raise RuntimeError(f"Clone {c.clone_id} has invalid parent {c.parent_id}")

        # Generation and root ancestor consistency
        for c in self.clones:
            if c.parent_id is None:
                if c.generation != 0:
                    raise RuntimeError(f"Root clone {c.clone_id} has generation {c.generation} != 0")
                if c.root_ancestor != c.clone_id:
                    raise RuntimeError(f"Root clone {c.clone_id} has root_ancestor {c.root_ancestor} != itself")
            else:
                parent = next((p for p in self.clones if p.clone_id == c.parent_id), None)
                if parent:
                    if c.generation != parent.generation + 1:
                        raise RuntimeError(f"Clone {c.clone_id} generation {c.generation} not parent+1")
                    if c.root_ancestor != parent.root_ancestor:
                        raise RuntimeError(f"Clone {c.clone_id} root_ancestor mismatch")

        # Total burden equals sum of populations
        total = sum(c.population for c in self.clones if c.alive)
        if not math.isclose(total, self.results.tumor_burden[-1] if self.results.tumor_burden else total, rel_tol=1e-9):
            raise RuntimeError(f"Total burden mismatch: computed {total}, recorded {self.results.tumor_burden[-1]}")

        # Frequencies sum to 1
        freqs = self.get_clone_frequencies()
        if freqs:
            freq_sum = sum(freqs.values())
            if not math.isclose(freq_sum, 1.0, rel_tol=1e-9):
                raise RuntimeError(f"Frequencies sum to {freq_sum}, not 1")

        # Diversity metrics finite
        for div in [self.results.shannon_diversity[-1] if self.results.shannon_diversity else 0,
                    self.results.simpson_diversity[-1] if self.results.simpson_diversity else 0]:
            if math.isnan(div) or math.isinf(div):
                raise RuntimeError("Diversity metric is NaN or Inf")

        # Mutation counts consistency
        for c in self.clones:
            if c.driver_mutation_count < 0 or c.passenger_mutation_count < 0:
                raise RuntimeError(f"Clone {c.clone_id} negative mutation counts")
        total_mut = self.results.driver_mutations + self.results.passenger_mutations
        if total_mut != len(self.results.mutations):
            raise RuntimeError(f"Mutation count mismatch: driver+passenger={total_mut}, recorded={len(self.results.mutations)}")
        if self.results.total_mutations < self.results.successful_establishments:
            raise RuntimeError("Total mutations less than successful establishments")

        # Lineage acyclicity
        self._check_lineage_cycles()

    def _check_lineage_cycles(self) -> None:
        visited = set()
        for clone in self.clones:
            if clone.clone_id in visited:
                continue
            current = clone
            chain = set()
            while current is not None:
                if current.clone_id in chain:
                    raise RuntimeError(f"Lineage cycle detected involving clone {current.clone_id}")
                chain.add(current.clone_id)
                if current.parent_id is None:
                    break
                parent = next((c for c in self.clones if c.clone_id == current.parent_id), None)
                if parent is None:
                    break
                current = parent
            visited.update(chain)

    # ----------------------------------------------------------------------
    # Lineage summary (unchanged)
    # ----------------------------------------------------------------------

    def _build_lineage_tree(self) -> Dict[int, List[int]]:
        tree = {}
        for c in self.clones:
            if c.parent_id is not None:
                tree.setdefault(c.parent_id, []).append(c.clone_id)
        return tree

    def _format_lineage_tree(self, tree: Dict[int, List[int]], node: int, prefix: str = "", is_last: bool = True) -> str:
        children = tree.get(node, [])
        if not children:
            return ""
        lines = []
        for i, child in enumerate(children):
            is_last_child = (i == len(children) - 1)
            connector = "└── " if is_last_child else "├── "
            lines.append(prefix + connector + f"Clone {child}")
            extension = "    " if is_last_child else "│   "
            lines.append(self._format_lineage_tree(tree, child, prefix + extension, is_last_child))
        return "\n".join(lines)

    def get_lineage_summary(self) -> str:
        roots = [c for c in self.clones if c.parent_id is None]
        if not roots:
            return "No roots found."
        tree = self._build_lineage_tree()
        lines = []
        for root in roots:
            lines.append(f"Clone {root.clone_id}")
            lines.append(self._format_lineage_tree(tree, root.clone_id, ""))
        return "\n".join(lines)

    # ----------------------------------------------------------------------
    # Main simulation loop
    # ----------------------------------------------------------------------

    def run(self) -> SimulationResults:
        """Execute the simulation for the configured number of time steps."""
        self.initialize_population()
        self.record(0)

        for t in range(1, self.cfg.time_steps + 1):
            self._current_time = t
            self.growth()
            self.mutate(t)
            self.death()            # death after mutation (natural cell death)
            # selection is implicit; we do not call selection()
            self.record(t)

        return self.results


# ----------------------------------------------------------------------
# Summary printing
# ----------------------------------------------------------------------

def print_summary(eng: TumorEvolutionEngine, res: SimulationResults) -> None:
    alive = [c for c in eng.clones if c.alive]
    extinct = [c for c in eng.clones if not c.alive]

    total_burden = res.tumor_burden[-1] if res.tumor_burden else 0.0
    max_burden = max(res.tumor_burden) if res.tumor_burden else 0.0
    final_shannon = res.shannon_diversity[-1] if res.shannon_diversity else 0.0
    final_simpson = res.simpson_diversity[-1] if res.simpson_diversity else 0.0

    max_age = max((c.age for c in eng.clones), default=0)
    if alive:
        mean_fitness = sum(c.fitness for c in alive) / len(alive)
        max_fitness = max(c.fitness for c in alive)
    else:
        mean_fitness = max_fitness = 0.0

    if alive:
        largest = max(alive, key=lambda c: c.population)
        smallest = min(alive, key=lambda c: c.population)
        largest_info = f"Clone {largest.clone_id} (pop={largest.population:.2f}, fit={largest.fitness:.3f})"
        smallest_info = f"Clone {smallest.clone_id} (pop={smallest.population:.2f}, fit={smallest.fitness:.3f})"
    else:
        largest_info = smallest_info = "None"

    print("=" * 60)
    print("Integrated Systems Oncology — Tumor Evolution Engine")
    print(f"Version: {ENGINE_VERSION}")
    print("=" * 60)
    print(f"Simulation mode: {'DEVELOPMENT' if eng.cfg.development_mode else 'PRODUCTION'}")
    print(f"Random seed: {eng.cfg.random_seed}")
    print(f"Time steps: {eng.cfg.time_steps}")
    print(f"Initial clones: {eng.cfg.initial_clone_count}")
    print(f"Living clones: {len(alive)}")
    print(f"Extinct clones: {len(extinct)}")
    print(f"Total tumor burden: {total_burden:.2f} (max: {max_burden:.2f})")
    print(f"Total mutations attempted: {res.total_mutations}")
    print(f"  Successful establishments: {res.successful_establishments}")
    print(f"  Failed establishments: {res.failed_establishments}")
    print(f"  Driver mutations: {res.driver_mutations}")
    print(f"  Passenger mutations: {res.passenger_mutations}")
    print(f"Shannon diversity: {final_shannon:.4f}")
    print(f"Simpson diversity: {final_simpson:.4f}")
    print(f"Maximum clone age: {max_age}")
    print(f"Mean fitness: {mean_fitness:.4f}")
    print(f"Maximum fitness: {max_fitness:.4f}")
    print(f"Largest living clone: {largest_info}")
    print(f"Smallest living clone: {smallest_info}")
    if res.extinct_clones:
        print(f"Extinct clones: {', '.join(str(cid) for cid in res.extinct_clones[:10])}" +
              ("..." if len(res.extinct_clones) > 10 else ""))
    print("-" * 60)
    print("Lineage summary (living clones):")
    lineage_str = eng.get_lineage_summary()
    if lineage_str:
        print(lineage_str)
    else:
        print("No living clones.")
    print("=" * 60)


def main() -> None:
    cfg = SimulationConfig()
    eng = TumorEvolutionEngine(cfg)
    res = eng.run()
    print_summary(eng, res)


if __name__ == "__main__":
    main()