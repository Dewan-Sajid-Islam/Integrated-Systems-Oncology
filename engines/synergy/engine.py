from __future__ import annotations
from dataclasses import dataclass, field
from typing import Optional, List, Dict, Tuple
from enum import IntEnum
import math
import numpy as np

ENGINE_VERSION = "1.0.0"


@dataclass
class SimulationConfig:
    """Configuration parameters for the synergy simulation."""

    # Core simulation parameters
    random_seed: int = 42
    time_steps: int = 100
    dt: float = 0.1
    num_regions: int = 10

    # Initial values (all in [0,1] where applicable)
    initial_tumor_fitness: float = 0.5
    initial_metabolic_fitness: float = 0.5
    initial_epigenetic_fitness: float = 0.5
    initial_stemness: float = 0.5
    initial_plasticity: float = 0.3
    initial_mutation_pressure: float = 0.1
    initial_selection_pressure: float = 0.3
    initial_metabolic_stress: float = 0.1
    initial_oxidative_stress: float = 0.1
    initial_hypoxia: float = 0.1
    initial_chromatin_accessibility: float = 0.5
    initial_gene_expression: float = 0.5
    initial_adaptive_capacity: float = 0.3
    initial_therapy_resistance: float = 0.1
    initial_cellular_resilience: float = 0.4
    initial_system_stability: float = 0.7

    # Rates and weights (revised for bounded dynamics)
    hypoxia_response_rate: float = 0.2
    hypoxia_decay_rate: float = 0.1
    oxidative_stress_response_rate: float = 0.15
    oxidative_stress_decay_rate: float = 0.1
    metabolic_stress_response_rate: float = 0.2
    metabolic_stress_decay_rate: float = 0.1
    mutation_response_rate: float = 0.15
    mutation_decay_rate: float = 0.08
    selection_response_rate: float = 0.1
    selection_decay_rate: float = 0.08
    plasticity_response_rate: float = 0.12
    plasticity_decay_rate: float = 0.08
    resistance_response_rate: float = 0.1
    resistance_decay_rate: float = 0.06
    chromatin_response_rate: float = 0.1
    gene_expression_response_rate: float = 0.12
    adaptive_response_rate: float = 0.1
    stemness_response_rate: float = 0.12
    resilience_response_rate: float = 0.1
    stability_response_rate: float = 0.08

    # Weights for stress composition
    hypoxia_metabolic_stress_weight: float = 0.5
    oxidative_stress_weight: float = 0.5

    # Weights for stress contributions to mutation
    metabolic_stress_mutation_weight: float = 0.6
    oxidative_stress_mutation_weight: float = 0.4

    # Additional coupling
    mutation_plasticity_weight: float = 0.4
    plasticity_resistance_weight: float = 0.3
    chromatin_expression_weight: float = 0.3
    expression_adaptive_weight: float = 0.3
    resilience_resistance_weight: float = 0.2
    stemness_resilience_weight: float = 0.2
    stability_resilience_weight: float = 0.2

    # Fitness costs (negative feedback)
    resistance_fitness_cost: float = 0.05
    mutation_fitness_cost: float = 0.05
    stress_stemness_reduction: float = 0.03
    stress_resilience_reduction: float = 0.03

    # Fitness combination weights
    tumor_fitness_weight: float = 0.4
    metabolic_fitness_weight: float = 0.3
    epigenetic_fitness_weight: float = 0.3

    # Heterogeneity scale
    heterogeneity_scale: float = 0.05

    # Development mode
    development_mode: bool = True
    development_dt_multiplier: float = 10.0

    # Validation
    strict_validation: bool = True


@dataclass
class SimulationResults:
    """Container for all recorded simulation data."""
    time: List[float] = field(default_factory=list)

    # Spatial histories (list of arrays per time step)
    tumor_fitness_hist: List[np.ndarray] = field(default_factory=list)
    metabolic_fitness_hist: List[np.ndarray] = field(default_factory=list)
    epigenetic_fitness_hist: List[np.ndarray] = field(default_factory=list)
    combined_fitness_hist: List[np.ndarray] = field(default_factory=list)
    stemness_hist: List[np.ndarray] = field(default_factory=list)
    plasticity_hist: List[np.ndarray] = field(default_factory=list)
    mutation_pressure_hist: List[np.ndarray] = field(default_factory=list)
    selection_pressure_hist: List[np.ndarray] = field(default_factory=list)
    metabolic_stress_hist: List[np.ndarray] = field(default_factory=list)
    oxidative_stress_hist: List[np.ndarray] = field(default_factory=list)
    hypoxia_hist: List[np.ndarray] = field(default_factory=list)
    chromatin_accessibility_hist: List[np.ndarray] = field(default_factory=list)
    gene_expression_hist: List[np.ndarray] = field(default_factory=list)
    adaptive_capacity_hist: List[np.ndarray] = field(default_factory=list)
    therapy_resistance_hist: List[np.ndarray] = field(default_factory=list)
    cellular_resilience_hist: List[np.ndarray] = field(default_factory=list)
    system_stability_hist: List[np.ndarray] = field(default_factory=list)

    # Scalar metrics per time step
    mean_combined_fitness: List[float] = field(default_factory=list)
    mean_mutation_pressure: List[float] = field(default_factory=list)
    mean_therapy_resistance: List[float] = field(default_factory=list)
    mean_adaptive_capacity: List[float] = field(default_factory=list)
    mean_resilience: List[float] = field(default_factory=list)
    mean_stability: List[float] = field(default_factory=list)
    mean_stemness: List[float] = field(default_factory=list)
    mean_plasticity: List[float] = field(default_factory=list)
    mean_metabolic_stress: List[float] = field(default_factory=list)
    mean_oxidative_stress: List[float] = field(default_factory=list)
    mean_hypoxia: List[float] = field(default_factory=list)

    # Summary statistics (computed at end)
    final_combined_fitness: float = 0.0
    final_mutation_pressure: float = 0.0
    final_therapy_resistance: float = 0.0
    final_adaptive_capacity: float = 0.0
    final_resilience: float = 0.0
    final_stability: float = 0.0
    final_stemness: float = 0.0
    final_plasticity: float = 0.0
    final_metabolic_stress: float = 0.0
    final_oxidative_stress: float = 0.0
    final_hypoxia: float = 0.0
    avg_combined_fitness: float = 0.0


class SynergyEngine:
    """
    Synergy Engine for the Integrated Systems Oncology framework.

    This engine models the interactions between tumour evolution, metabolism,
    and epigenetics. It computes combined fitness and emergent properties such
    as therapy resistance, adaptive capacity, and system stability. The dynamics
    use bounded growth terms to prevent saturation and ensure intermediate values.
    """

    def __init__(self, cfg: SimulationConfig):
        self.cfg = cfg
        self.rng = np.random.default_rng(cfg.random_seed)
        self.results = SimulationResults()
        self._validate_config()

        n = cfg.num_regions
        # State arrays
        self.tumor_fitness: np.ndarray = np.zeros(n)
        self.metabolic_fitness: np.ndarray = np.zeros(n)
        self.epigenetic_fitness: np.ndarray = np.zeros(n)
        self.combined_fitness: np.ndarray = np.zeros(n)
        self.stemness: np.ndarray = np.zeros(n)
        self.plasticity: np.ndarray = np.zeros(n)
        self.mutation_pressure: np.ndarray = np.zeros(n)
        self.selection_pressure: np.ndarray = np.zeros(n)
        self.metabolic_stress: np.ndarray = np.zeros(n)
        self.oxidative_stress: np.ndarray = np.zeros(n)
        self.hypoxia: np.ndarray = np.zeros(n)
        self.chromatin_accessibility: np.ndarray = np.zeros(n)
        self.gene_expression: np.ndarray = np.zeros(n)
        self.adaptive_capacity: np.ndarray = np.zeros(n)
        self.therapy_resistance: np.ndarray = np.zeros(n)
        self.cellular_resilience: np.ndarray = np.zeros(n)
        self.system_stability: np.ndarray = np.zeros(n)

        self._current_time: float = 0.0
        self._heterogeneity_mask: Optional[np.ndarray] = None

    def _validate_config(self) -> None:
        cfg = self.cfg
        if cfg.time_steps < 1:
            raise ValueError("time_steps must be at least 1")
        if cfg.dt <= 0:
            raise ValueError("dt must be positive")
        if cfg.num_regions < 1:
            raise ValueError("num_regions must be at least 1")
        # Validate initial values
        for name, val in [
            ("initial_tumor_fitness", cfg.initial_tumor_fitness),
            ("initial_metabolic_fitness", cfg.initial_metabolic_fitness),
            ("initial_epigenetic_fitness", cfg.initial_epigenetic_fitness),
            ("initial_stemness", cfg.initial_stemness),
            ("initial_plasticity", cfg.initial_plasticity),
            ("initial_mutation_pressure", cfg.initial_mutation_pressure),
            ("initial_selection_pressure", cfg.initial_selection_pressure),
            ("initial_metabolic_stress", cfg.initial_metabolic_stress),
            ("initial_oxidative_stress", cfg.initial_oxidative_stress),
            ("initial_hypoxia", cfg.initial_hypoxia),
            ("initial_chromatin_accessibility", cfg.initial_chromatin_accessibility),
            ("initial_gene_expression", cfg.initial_gene_expression),
            ("initial_adaptive_capacity", cfg.initial_adaptive_capacity),
            ("initial_therapy_resistance", cfg.initial_therapy_resistance),
            ("initial_cellular_resilience", cfg.initial_cellular_resilience),
            ("initial_system_stability", cfg.initial_system_stability)
        ]:
            if not (0 <= val <= 1):
                raise ValueError(f"{name} must be between 0 and 1")
        # Rates and weights: ensure non-negative
        for attr in ['hypoxia_response_rate', 'hypoxia_decay_rate',
                     'oxidative_stress_response_rate', 'oxidative_stress_decay_rate',
                     'metabolic_stress_response_rate', 'metabolic_stress_decay_rate',
                     'mutation_response_rate', 'mutation_decay_rate',
                     'selection_response_rate', 'selection_decay_rate',
                     'plasticity_response_rate', 'plasticity_decay_rate',
                     'resistance_response_rate', 'resistance_decay_rate',
                     'chromatin_response_rate', 'gene_expression_response_rate',
                     'adaptive_response_rate', 'stemness_response_rate',
                     'resilience_response_rate', 'stability_response_rate',
                     'hypoxia_metabolic_stress_weight', 'oxidative_stress_weight',
                     'metabolic_stress_mutation_weight', 'oxidative_stress_mutation_weight',
                     'mutation_plasticity_weight', 'plasticity_resistance_weight',
                     'chromatin_expression_weight', 'expression_adaptive_weight',
                     'resilience_resistance_weight', 'stemness_resilience_weight',
                     'stability_resilience_weight', 'resistance_fitness_cost',
                     'mutation_fitness_cost', 'stress_stemness_reduction',
                     'stress_resilience_reduction']:
            if getattr(cfg, attr) < 0:
                raise ValueError(f"{attr} must be non-negative")

    def _generate_heterogeneity(self) -> np.ndarray:
        """Generate a deterministic heterogeneity mask using the RNG."""
        n = self.cfg.num_regions
        offsets = self.rng.normal(0, 1.0, size=n)
        offsets = np.clip(offsets, -2.0, 2.0)
        return offsets * self.cfg.heterogeneity_scale

    def initialize_state(self) -> None:
        """Set initial state from configuration with region heterogeneity."""
        cfg = self.cfg
        n = cfg.num_regions
        self._heterogeneity_mask = self._generate_heterogeneity()

        def apply_heterogeneity(base_val: float) -> np.ndarray:
            val = base_val + self._heterogeneity_mask
            return np.clip(val, 0.0, 1.0)

        self.tumor_fitness = apply_heterogeneity(cfg.initial_tumor_fitness)
        self.metabolic_fitness = apply_heterogeneity(cfg.initial_metabolic_fitness)
        self.epigenetic_fitness = apply_heterogeneity(cfg.initial_epigenetic_fitness)
        self.stemness = apply_heterogeneity(cfg.initial_stemness)
        self.plasticity = apply_heterogeneity(cfg.initial_plasticity)
        self.mutation_pressure = apply_heterogeneity(cfg.initial_mutation_pressure)
        self.selection_pressure = apply_heterogeneity(cfg.initial_selection_pressure)
        self.metabolic_stress = apply_heterogeneity(cfg.initial_metabolic_stress)
        self.oxidative_stress = apply_heterogeneity(cfg.initial_oxidative_stress)
        self.hypoxia = apply_heterogeneity(cfg.initial_hypoxia)
        self.chromatin_accessibility = apply_heterogeneity(cfg.initial_chromatin_accessibility)
        self.gene_expression = apply_heterogeneity(cfg.initial_gene_expression)
        self.adaptive_capacity = apply_heterogeneity(cfg.initial_adaptive_capacity)
        self.therapy_resistance = apply_heterogeneity(cfg.initial_therapy_resistance)
        self.cellular_resilience = apply_heterogeneity(cfg.initial_cellular_resilience)
        self.system_stability = apply_heterogeneity(cfg.initial_system_stability)

        # Compute combined fitness
        self.combined_fitness = (cfg.tumor_fitness_weight * self.tumor_fitness +
                                 cfg.metabolic_fitness_weight * self.metabolic_fitness +
                                 cfg.epigenetic_fitness_weight * self.epigenetic_fitness)

        self._current_time = 0.0
        self.results = SimulationResults()

    def _step(self) -> None:
        """Perform one integration step with bounded dynamics."""
        cfg = self.cfg
        dt = cfg.dt
        if cfg.development_mode:
            dt *= cfg.development_dt_multiplier

        # Current arrays
        tf = self.tumor_fitness
        mf = self.metabolic_fitness
        ef = self.epigenetic_fitness
        stem = self.stemness
        plas = self.plasticity
        mut = self.mutation_pressure
        sel = self.selection_pressure
        met_stress = self.metabolic_stress
        ox_stress = self.oxidative_stress
        hyp = self.hypoxia
        chrom = self.chromatin_accessibility
        gene = self.gene_expression
        adapt = self.adaptive_capacity
        resist = self.therapy_resistance
        resil = self.cellular_resilience
        stab = self.system_stability

        # 1. Hypoxia: driven by metabolic stress, bounded growth + decay
        # dx/dt = rate * met_stress * (1 - x) - decay * x
        hyp_delta = (cfg.hypoxia_response_rate * met_stress * (1 - hyp) -
                     cfg.hypoxia_decay_rate * hyp) * dt
        hyp_new = np.clip(hyp + hyp_delta, 0.0, 1.0)

        # 2. Oxidative stress: driven by metabolic fitness, bounded growth + decay
        ox_delta = (cfg.oxidative_stress_response_rate * mf * (1 - ox_stress) -
                    cfg.oxidative_stress_decay_rate * ox_stress) * dt
        ox_new = np.clip(ox_stress + ox_delta, 0.0, 1.0)

        # 3. Metabolic stress: weighted combination of hypoxia and oxidative stress with its own dynamics
        target_met_stress = (cfg.hypoxia_metabolic_stress_weight * hyp_new +
                             cfg.oxidative_stress_weight * ox_new)
        met_delta = (cfg.metabolic_stress_response_rate * target_met_stress * (1 - met_stress) -
                     cfg.metabolic_stress_decay_rate * met_stress) * dt
        met_stress_new = np.clip(met_stress + met_delta, 0.0, 1.0)

        # 4. Mutation pressure: driven by stresses, bounded growth + decay
        mut_drive = (cfg.metabolic_stress_mutation_weight * met_stress_new +
                     cfg.oxidative_stress_mutation_weight * ox_new)
        mut_delta = (cfg.mutation_response_rate * mut_drive * (1 - mut) -
                     cfg.mutation_decay_rate * mut) * dt
        mut_new = np.clip(mut + mut_delta, 0.0, 1.0)

        # 5. Selection pressure: driven by combined fitness and hypoxia, bounded growth + decay
        sel_drive = (0.2 * self.combined_fitness + 0.1 * hyp_new) * (1 - 0.3 * resist)
        sel_delta = (cfg.selection_response_rate * sel_drive * (1 - sel) -
                     cfg.selection_decay_rate * sel) * dt
        sel_new = np.clip(sel + sel_delta, 0.0, 1.0)

        # 6. Plasticity: driven by mutation pressure, bounded growth + decay
        plas_delta = (cfg.mutation_plasticity_weight * cfg.mutation_plasticity_weight * mut_new * (1 - plas) -
                      cfg.plasticity_decay_rate * plas) * dt
        plas_new = np.clip(plas + plas_delta, 0.0, 1.0)

        # 7. Therapy resistance: driven by plasticity and resilience, bounded growth + decay
        resist_drive = (cfg.plasticity_resistance_weight * plas_new +
                        cfg.resilience_resistance_weight * resil)
        resist_delta = (cfg.resistance_response_rate * resist_drive * (1 - resist) -
                        cfg.resistance_decay_rate * resist) * dt
        resist_new = np.clip(resist + resist_delta, 0.0, 1.0)

        # 8. Chromatin accessibility: influenced by plasticity, bounded
        chrom_target = 0.5 + 0.4 * plas_new
        chrom_delta = (cfg.chromatin_response_rate * (chrom_target - chrom)) * dt
        chrom_new = np.clip(chrom + chrom_delta, 0.0, 1.0)

        # 9. Gene expression: driven by chromatin, bounded growth + decay
        gene_delta = (cfg.chromatin_expression_weight * cfg.chromatin_expression_weight * chrom_new * (1 - gene) -
                      0.02 * gene) * dt
        gene_new = np.clip(gene + gene_delta, 0.0, 1.0)

        # 10. Adaptive capacity: driven by gene expression, bounded saturation
        adapt_delta = (cfg.expression_adaptive_weight * cfg.expression_adaptive_weight * gene_new * (1 - adapt) -
                       0.02 * adapt) * dt
        adapt_new = np.clip(adapt + adapt_delta, 0.0, 1.0)

        # 11. Stemness: increases with resilience, decreases with plasticity and stress
        stem_delta = (cfg.stemness_resilience_weight * resil * (1 - stem) -
                      0.03 * plas_new * stem -
                      cfg.stress_stemness_reduction * met_stress_new * stem) * dt
        stem_new = np.clip(stem + stem_delta, 0.0, 1.0)

        # 12. Cellular resilience: increases with stemness, decreases with stress
        resil_delta = (cfg.stemness_resilience_weight * stem_new * (1 - resil) -
                       cfg.stress_resilience_reduction * met_stress_new * resil -
                       0.01 * ox_new * resil) * dt
        resil_new = np.clip(resil + resil_delta, 0.0, 1.0)

        # 13. System stability: increases with resilience, decreases with oxidative stress and mutation
        stab_delta = (cfg.stability_resilience_weight * resil_new * (1 - stab) -
                      0.06 * ox_new * stab -
                      0.04 * mut_new * stab) * dt
        stab_new = np.clip(stab + stab_delta, 0.0, 1.0)

        # 14. Fitness components: influenced by stresses and resistance costs
        tf_delta = (0.02 * (1 - tf) * (1 - 0.5 * met_stress_new) -
                    0.02 * cfg.resistance_fitness_cost * resist * tf) * dt
        tf_new = np.clip(tf + tf_delta, 0.0, 1.0)

        mf_delta = (0.02 * (1 - mf) * (1 - 0.5 * ox_new) -
                    0.02 * mut_new * mf) * dt
        mf_new = np.clip(mf + mf_delta, 0.0, 1.0)

        ef_delta = (0.02 * (1 - ef) * (1 - 0.5 * mut_new) -
                    0.02 * cfg.mutation_fitness_cost * mut_new * ef) * dt
        ef_new = np.clip(ef + ef_delta, 0.0, 1.0)

        # 15. Combined fitness
        comb_fit = (cfg.tumor_fitness_weight * tf_new +
                    cfg.metabolic_fitness_weight * mf_new +
                    cfg.epigenetic_fitness_weight * ef_new)

        # Update state
        self.tumor_fitness = tf_new
        self.metabolic_fitness = mf_new
        self.epigenetic_fitness = ef_new
        self.combined_fitness = comb_fit
        self.stemness = stem_new
        self.plasticity = plas_new
        self.mutation_pressure = mut_new
        self.selection_pressure = sel_new
        self.metabolic_stress = met_stress_new
        self.oxidative_stress = ox_new
        self.hypoxia = hyp_new
        self.chromatin_accessibility = chrom_new
        self.gene_expression = gene_new
        self.adaptive_capacity = adapt_new
        self.therapy_resistance = resist_new
        self.cellular_resilience = resil_new
        self.system_stability = stab_new

        self._current_time += dt

    def record(self) -> None:
        """Record current state into results."""
        res = self.results
        res.time.append(self._current_time)
        res.tumor_fitness_hist.append(self.tumor_fitness.copy())
        res.metabolic_fitness_hist.append(self.metabolic_fitness.copy())
        res.epigenetic_fitness_hist.append(self.epigenetic_fitness.copy())
        res.combined_fitness_hist.append(self.combined_fitness.copy())
        res.stemness_hist.append(self.stemness.copy())
        res.plasticity_hist.append(self.plasticity.copy())
        res.mutation_pressure_hist.append(self.mutation_pressure.copy())
        res.selection_pressure_hist.append(self.selection_pressure.copy())
        res.metabolic_stress_hist.append(self.metabolic_stress.copy())
        res.oxidative_stress_hist.append(self.oxidative_stress.copy())
        res.hypoxia_hist.append(self.hypoxia.copy())
        res.chromatin_accessibility_hist.append(self.chromatin_accessibility.copy())
        res.gene_expression_hist.append(self.gene_expression.copy())
        res.adaptive_capacity_hist.append(self.adaptive_capacity.copy())
        res.therapy_resistance_hist.append(self.therapy_resistance.copy())
        res.cellular_resilience_hist.append(self.cellular_resilience.copy())
        res.system_stability_hist.append(self.system_stability.copy())

        # Scalar metrics
        res.mean_combined_fitness.append(np.mean(self.combined_fitness))
        res.mean_mutation_pressure.append(np.mean(self.mutation_pressure))
        res.mean_therapy_resistance.append(np.mean(self.therapy_resistance))
        res.mean_adaptive_capacity.append(np.mean(self.adaptive_capacity))
        res.mean_resilience.append(np.mean(self.cellular_resilience))
        res.mean_stability.append(np.mean(self.system_stability))
        res.mean_stemness.append(np.mean(self.stemness))
        res.mean_plasticity.append(np.mean(self.plasticity))
        res.mean_metabolic_stress.append(np.mean(self.metabolic_stress))
        res.mean_oxidative_stress.append(np.mean(self.oxidative_stress))
        res.mean_hypoxia.append(np.mean(self.hypoxia))

    def validate_state(self) -> None:
        """Perform internal consistency checks."""
        n = self.cfg.num_regions
        for arr, name in [
            (self.tumor_fitness, "tumor_fitness"),
            (self.metabolic_fitness, "metabolic_fitness"),
            (self.epigenetic_fitness, "epigenetic_fitness"),
            (self.combined_fitness, "combined_fitness"),
            (self.stemness, "stemness"),
            (self.plasticity, "plasticity"),
            (self.mutation_pressure, "mutation_pressure"),
            (self.selection_pressure, "selection_pressure"),
            (self.metabolic_stress, "metabolic_stress"),
            (self.oxidative_stress, "oxidative_stress"),
            (self.hypoxia, "hypoxia"),
            (self.chromatin_accessibility, "chromatin_accessibility"),
            (self.gene_expression, "gene_expression"),
            (self.adaptive_capacity, "adaptive_capacity"),
            (self.therapy_resistance, "therapy_resistance"),
            (self.cellular_resilience, "cellular_resilience"),
            (self.system_stability, "system_stability")
        ]:
            if arr.shape != (n,):
                raise RuntimeError(f"{name} array shape mismatch")
            if not np.all(np.isfinite(arr)):
                raise RuntimeError(f"{name} contains NaN or Inf")
            if np.any(arr < 0) or np.any(arr > 1 + 1e-6):
                raise RuntimeError(f"{name} out of [0,1] range")
        # Check history lengths
        n_steps = len(self.results.time)
        for hist in [
            self.results.tumor_fitness_hist,
            self.results.metabolic_fitness_hist,
            self.results.epigenetic_fitness_hist,
            self.results.combined_fitness_hist,
            self.results.stemness_hist,
            self.results.plasticity_hist,
            self.results.mutation_pressure_hist,
            self.results.selection_pressure_hist,
            self.results.metabolic_stress_hist,
            self.results.oxidative_stress_hist,
            self.results.hypoxia_hist,
            self.results.chromatin_accessibility_hist,
            self.results.gene_expression_hist,
            self.results.adaptive_capacity_hist,
            self.results.therapy_resistance_hist,
            self.results.cellular_resilience_hist,
            self.results.system_stability_hist
        ]:
            if len(hist) != n_steps:
                raise RuntimeError("History length mismatch")

    # ----------------------------------------------------------------------
    # Public API
    # ----------------------------------------------------------------------

    def get_combined_fitness(self) -> np.ndarray:
        return self.combined_fitness

    def get_region_combined_fitness(self, region: int) -> float:
        if region < 0 or region >= self.cfg.num_regions:
            raise IndexError("Region index out of bounds")
        return float(self.combined_fitness[region])

    def get_average_combined_fitness(self) -> float:
        return float(np.mean(self.combined_fitness))

    def run(self) -> SimulationResults:
        """Execute the simulation for the configured number of time steps."""
        self.initialize_state()
        self.record()

        for _ in range(self.cfg.time_steps):
            self._step()
            self.record()
            if self.cfg.strict_validation:
                self.validate_state()

        # Compute summary statistics
        res = self.results
        res.final_combined_fitness = np.mean(self.combined_fitness)
        res.final_mutation_pressure = np.mean(self.mutation_pressure)
        res.final_therapy_resistance = np.mean(self.therapy_resistance)
        res.final_adaptive_capacity = np.mean(self.adaptive_capacity)
        res.final_resilience = np.mean(self.cellular_resilience)
        res.final_stability = np.mean(self.system_stability)
        res.final_stemness = np.mean(self.stemness)
        res.final_plasticity = np.mean(self.plasticity)
        res.final_metabolic_stress = np.mean(self.metabolic_stress)
        res.final_oxidative_stress = np.mean(self.oxidative_stress)
        res.final_hypoxia = np.mean(self.hypoxia)
        res.avg_combined_fitness = np.mean(res.mean_combined_fitness) if res.mean_combined_fitness else 0.0

        return self.results


def print_summary(eng: SynergyEngine, res: SimulationResults) -> None:
    """Print a comprehensive end‑of‑run summary."""
    print("=" * 60)
    print("Integrated Systems Oncology — Synergy Engine")
    print(f"Version: {ENGINE_VERSION}")
    print("=" * 60)
    print(f"Simulation mode: {'DEVELOPMENT' if eng.cfg.development_mode else 'PRODUCTION'}")
    print(f"Random seed: {eng.cfg.random_seed}")
    print(f"Time steps: {eng.cfg.time_steps}")
    print(f"Number of regions: {eng.cfg.num_regions}")
    print(f"Average combined fitness: {res.final_combined_fitness:.4f}")
    print(f"Average mutation pressure: {res.final_mutation_pressure:.4f}")
    print(f"Average therapy resistance: {res.final_therapy_resistance:.4f}")
    print(f"Average adaptive capacity: {res.final_adaptive_capacity:.4f}")
    print(f"Average cellular resilience: {res.final_resilience:.4f}")
    print(f"Average system stability: {res.final_stability:.4f}")
    print(f"Average stemness: {res.final_stemness:.4f}")
    print(f"Average plasticity: {res.final_plasticity:.4f}")
    print(f"Average metabolic stress: {res.final_metabolic_stress:.4f}")
    print(f"Average oxidative stress: {res.final_oxidative_stress:.4f}")
    print(f"Average hypoxia: {res.final_hypoxia:.4f}")
    print(f"Overall average combined fitness: {res.avg_combined_fitness:.4f}")
    print("-" * 60)
    print("Spatial variation at final time:")
    for var, arr in [
        ("Combined fitness", eng.combined_fitness),
        ("Mutation pressure", eng.mutation_pressure),
        ("Resistance", eng.therapy_resistance),
        ("Stemness", eng.stemness)
    ]:
        print(f"  {var}: min={arr.min():.4f}, max={arr.max():.4f}, mean={arr.mean():.4f}")
    print("=" * 60)


def main() -> None:
    """Example usage of the Synergy Engine."""
    cfg = SimulationConfig()
    eng = SynergyEngine(cfg)
    res = eng.run()
    print_summary(eng, res)


if __name__ == "__main__":
    main()