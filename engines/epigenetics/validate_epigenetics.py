from __future__ import annotations
from dataclasses import dataclass, field
from enum import IntEnum
from typing import Optional, List, Dict, Tuple
import math
import numpy as np

ENGINE_VERSION = "1.0.0"


class DifferentiationState(IntEnum):
    """Differentiation state categories."""
    UNDIFFERENTIATED = 0
    PROGENITOR = 1
    DIFFERENTIATED = 2
    TERMINALLY_DIFFERENTIATED = 3


class ChromatinState(IntEnum):
    """Chromatin state categories."""
    CLOSED = 0
    INTERMEDIATE = 1
    OPEN = 2


@dataclass
class SimulationConfig:
    """Configuration parameters for the epigenetics simulation."""

    # Core simulation parameters
    random_seed: int = 42
    time_steps: int = 100
    dt: float = 0.1
    num_regions: int = 10

    # DNA methylation dynamics
    methylation_drift_rate: float = 0.01        # passive drift towards equilibrium
    methylation_equilibrium: float = 0.5        # equilibrium methylation level
    demethylation_rate: float = 0.02            # active demethylation
    methylation_stress_effect: float = 0.05     # stress-induced methylation change

    # Histone acetylation dynamics
    acetylation_rate: float = 0.03              # histone acetyltransferase activity
    deacetylation_rate: float = 0.02            # histone deacetylase activity
    acetylation_equilibrium: float = 0.5
    acetylation_stress_effect: float = 0.04

    # Chromatin accessibility dynamics
    accessibility_opening_rate: float = 0.04    # opening rate (acetylation dependent)
    accessibility_closing_rate: float = 0.02    # closing rate (methylation dependent)
    accessibility_base: float = 0.3

    # Gene expression potential
    expression_base: float = 0.2
    expression_acetylation_factor: float = 1.5
    expression_methylation_factor: float = -1.0
    expression_accessibility_factor: float = 1.0
    expression_noise: float = 0.02

    # Epigenetic instability
    instability_base: float = 0.05
    instability_stress_factor: float = 1.5
    instability_decay: float = 0.01

    # Plasticity
    plasticity_base: float = 0.2
    plasticity_instability_factor: float = 0.5
    plasticity_decay: float = 0.01

    # Stemness
    stemness_base: float = 0.5
    stemness_differentiation_rate: float = 0.02
    stemness_plasticity_factor: float = 0.3
    stemness_stress_factor: float = -0.2

    # Differentiation
    differentiation_rate: float = 0.02
    differentiation_stemness_threshold: float = 0.3

    # Epigenetic age
    age_accumulation_rate: float = 0.01
    age_reset_fraction: float = 0.1          # reset on high plasticity

    # Stress (environmental)
    stress_base: float = 0.1
    stress_instability_factor: float = 0.3
    stress_decay: float = 0.02

    # Initial conditions
    initial_methylation: float = 0.5
    initial_acetylation: float = 0.5
    initial_accessibility: float = 0.5
    initial_expression: float = 0.5
    initial_instability: float = 0.05
    initial_plasticity: float = 0.2
    initial_stemness: float = 0.5
    initial_differentiation: float = 0.0   # 0 = undifferentiated
    initial_stress: float = 0.1
    initial_epigenetic_age: float = 0.0

    # Validation
    strict_validation: bool = True
    development_mode: bool = True
    development_dt_multiplier: float = 10.0


@dataclass
class SimulationResults:
    """Container for all recorded simulation data."""
    time: List[float] = field(default_factory=list)

    # Spatial histories
    methylation_hist: List[np.ndarray] = field(default_factory=list)
    acetylation_hist: List[np.ndarray] = field(default_factory=list)
    accessibility_hist: List[np.ndarray] = field(default_factory=list)
    expression_hist: List[np.ndarray] = field(default_factory=list)
    instability_hist: List[np.ndarray] = field(default_factory=list)
    plasticity_hist: List[np.ndarray] = field(default_factory=list)
    stemness_hist: List[np.ndarray] = field(default_factory=list)
    differentiation_hist: List[np.ndarray] = field(default_factory=list)
    stress_hist: List[np.ndarray] = field(default_factory=list)
    epigenetic_age_hist: List[np.ndarray] = field(default_factory=list)

    # Scalar metrics per time step
    mean_methylation: List[float] = field(default_factory=list)
    mean_acetylation: List[float] = field(default_factory=list)
    mean_accessibility: List[float] = field(default_factory=list)
    mean_expression: List[float] = field(default_factory=list)
    mean_instability: List[float] = field(default_factory=list)
    mean_plasticity: List[float] = field(default_factory=list)
    mean_stemness: List[float] = field(default_factory=list)
    mean_differentiation: List[float] = field(default_factory=list)
    mean_stress: List[float] = field(default_factory=list)
    mean_epigenetic_age: List[float] = field(default_factory=list)

    # Summary statistics (computed at end)
    final_methylation: float = 0.0
    final_acetylation: float = 0.0
    final_accessibility: float = 0.0
    final_expression: float = 0.0
    final_instability: float = 0.0
    final_plasticity: float = 0.0
    final_stemness: float = 0.0
    final_differentiation: float = 0.0
    final_stress: float = 0.0
    final_epigenetic_age: float = 0.0
    avg_fitness: float = 0.0

    # Distributions at end
    differentiation_dist: Dict[int, int] = field(default_factory=dict)
    stemness_dist: Dict[float, int] = field(default_factory=dict)  # binned
    chromatin_dist: Dict[int, int] = field(default_factory=dict)


class EpigeneticsEngine:
    """
    Epigenetics Engine for the Integrated Systems Oncology framework.

    This engine models dynamic epigenetic regulation across multiple spatial regions.
    It tracks DNA methylation, histone acetylation, chromatin accessibility,
    gene expression potential, instability, plasticity, stemness, differentiation,
    stress, and epigenetic age. These variables interact through biologically
    motivated rules, including stochastic noise and feedback loops.

    Version 1.0.0 implements a comprehensive dynamic model suitable for
    integration with other ISO engines.
    """

    def __init__(self, cfg: SimulationConfig):
        self.cfg = cfg
        self.rng = np.random.default_rng(cfg.random_seed)
        self.results = SimulationResults()
        self._validate_config()

        n = cfg.num_regions
        self.methylation: np.ndarray = np.zeros(n)
        self.acetylation: np.ndarray = np.zeros(n)
        self.accessibility: np.ndarray = np.zeros(n)
        self.expression: np.ndarray = np.zeros(n)
        self.instability: np.ndarray = np.zeros(n)
        self.plasticity: np.ndarray = np.zeros(n)
        self.stemness: np.ndarray = np.zeros(n)
        self.differentiation: np.ndarray = np.zeros(n)
        self.stress: np.ndarray = np.zeros(n)
        self.epigenetic_age: np.ndarray = np.zeros(n)

        # Derived discrete states
        self.diff_state: np.ndarray = np.full(n, DifferentiationState.UNDIFFERENTIATED, dtype=np.int8)
        self.chromatin_state: np.ndarray = np.full(n, ChromatinState.INTERMEDIATE, dtype=np.int8)

        # Time tracking
        self._current_time: float = 0.0

    def _validate_config(self) -> None:
        cfg = self.cfg
        if cfg.time_steps < 1:
            raise ValueError("time_steps must be at least 1")
        if cfg.dt <= 0:
            raise ValueError("dt must be positive")
        if cfg.num_regions < 1:
            raise ValueError("num_regions must be at least 1")
        if cfg.methylation_drift_rate < 0 or cfg.demethylation_rate < 0:
            raise ValueError("methylation rates must be non-negative")
        if cfg.acetylation_rate < 0 or cfg.deacetylation_rate < 0:
            raise ValueError("acetylation rates must be non-negative")
        if cfg.accessibility_opening_rate < 0 or cfg.accessibility_closing_rate < 0:
            raise ValueError("accessibility rates must be non-negative")
        if cfg.instability_base < 0 or cfg.instability_decay < 0:
            raise ValueError("instability parameters must be non-negative")
        if cfg.plasticity_base < 0 or cfg.plasticity_decay < 0:
            raise ValueError("plasticity parameters must be non-negative")
        if cfg.stemness_base < 0 or cfg.stemness_differentiation_rate < 0:
            raise ValueError("stemness parameters must be non-negative")
        if cfg.differentiation_rate < 0:
            raise ValueError("differentiation_rate must be non-negative")
        if cfg.age_accumulation_rate < 0 or cfg.age_reset_fraction < 0:
            raise ValueError("age parameters must be non-negative")
        if cfg.stress_base < 0 or cfg.stress_decay < 0:
            raise ValueError("stress parameters must be non-negative")
        if cfg.initial_methylation < 0 or cfg.initial_methylation > 1:
            raise ValueError("initial_methylation must be between 0 and 1")
        if cfg.initial_acetylation < 0 or cfg.initial_acetylation > 1:
            raise ValueError("initial_acetylation must be between 0 and 1")
        if cfg.initial_accessibility < 0 or cfg.initial_accessibility > 1:
            raise ValueError("initial_accessibility must be between 0 and 1")
        if cfg.initial_expression < 0:
            raise ValueError("initial_expression must be non-negative")
        if cfg.initial_instability < 0:
            raise ValueError("initial_instability must be non-negative")
        if cfg.initial_plasticity < 0:
            raise ValueError("initial_plasticity must be non-negative")
        if cfg.initial_stemness < 0 or cfg.initial_stemness > 1:
            raise ValueError("initial_stemness must be between 0 and 1")
        if cfg.initial_differentiation < 0 or cfg.initial_differentiation > 1:
            raise ValueError("initial_differentiation must be between 0 and 1")
        if cfg.initial_stress < 0:
            raise ValueError("initial_stress must be non-negative")
        if cfg.initial_epigenetic_age < 0:
            raise ValueError("initial_epigenetic_age must be non-negative")

    def initialize_state(self) -> None:
        """Set initial concentrations and reset results."""
        n = self.cfg.num_regions
        self.methylation.fill(self.cfg.initial_methylation)
        self.acetylation.fill(self.cfg.initial_acetylation)
        self.accessibility.fill(self.cfg.initial_accessibility)
        self.expression.fill(self.cfg.initial_expression)
        self.instability.fill(self.cfg.initial_instability)
        self.plasticity.fill(self.cfg.initial_plasticity)
        self.stemness.fill(self.cfg.initial_stemness)
        self.differentiation.fill(self.cfg.initial_differentiation)
        self.stress.fill(self.cfg.initial_stress)
        self.epigenetic_age.fill(self.cfg.initial_epigenetic_age)

        self.diff_state.fill(DifferentiationState.UNDIFFERENTIATED)
        self.chromatin_state.fill(ChromatinState.INTERMEDIATE)
        self._current_time = 0.0
        self.results = SimulationResults()

    def _step(self) -> None:
        """Perform one simulation step using explicit Euler integration."""
        cfg = self.cfg
        dt = cfg.dt
        if cfg.development_mode:
            dt *= cfg.development_dt_multiplier

        # Current state
        met = self.methylation
        ace = self.acetylation
        acc = self.accessibility
        exp = self.expression
        inst = self.instability
        plas = self.plasticity
        stem = self.stemness
        diff = self.differentiation
        stress = self.stress
        age = self.epigenetic_age

        # 1. Stress dynamics
        # Stress increases with instability and decays towards base
        stress_new = stress + cfg.stress_base * dt
        stress_new += cfg.stress_instability_factor * inst * dt
        stress_new -= cfg.stress_decay * stress * dt
        stress_new = np.clip(stress_new, 0.0, 1.0)

        # 2. DNA methylation
        # Passive drift towards equilibrium, active demethylation, stress effect
        drift = cfg.methylation_drift_rate * (cfg.methylation_equilibrium - met) * dt
        demethyl = cfg.demethylation_rate * ace * (1 - met) * dt  # acetylation promotes demethylation
        stress_meth = cfg.methylation_stress_effect * stress_new * (0.5 - met) * dt
        met_new = met + drift + demethyl + stress_meth
        met_new = np.clip(met_new, 0.0, 1.0)

        # 3. Histone acetylation
        # Acetylation and deacetylation, stress effect
        acet_rate = cfg.acetylation_rate * (1 - ace) * dt
        deacet = cfg.deacetylation_rate * ace * dt
        stress_ace = cfg.acetylation_stress_effect * stress_new * (0.5 - ace) * dt
        ace_new = ace + acet_rate - deacet + stress_ace
        ace_new = np.clip(ace_new, 0.0, 1.0)

        # 4. Chromatin accessibility
        # Opening depends on acetylation, closing on methylation
        open_rate = cfg.accessibility_opening_rate * ace_new * (1 - acc) * dt
        close_rate = cfg.accessibility_closing_rate * met_new * acc * dt
        acc_new = acc + open_rate - close_rate
        acc_new = np.clip(acc_new, 0.0, 1.0)

        # 5. Gene expression potential
        # Influenced by acetylation (positive), methylation (negative), accessibility (positive)
        expr_factor = (cfg.expression_base +
                       cfg.expression_acetylation_factor * ace_new +
                       cfg.expression_methylation_factor * met_new +
                       cfg.expression_accessibility_factor * acc_new)
        # Noise
        noise = self.rng.normal(0, cfg.expression_noise, size=len(met))
        exp_new = np.clip(expr_factor + noise, 0.0, None)

        # 6. Epigenetic instability
        # Increases with stress, decays towards base
        inst_new = inst + cfg.instability_base * dt
        inst_new += cfg.instability_stress_factor * stress_new * dt
        inst_new -= cfg.instability_decay * inst * dt
        inst_new = np.clip(inst_new, 0.0, 1.0)

        # 7. Plasticity
        # Increases with instability, decays towards base
        plas_new = plas + cfg.plasticity_base * dt
        plas_new += cfg.plasticity_instability_factor * inst_new * dt
        plas_new -= cfg.plasticity_decay * plas * dt
        plas_new = np.clip(plas_new, 0.0, 1.0)

        # 8. Stemness
        # Decreases with differentiation, influenced by plasticity and stress
        stem_new = stem - cfg.stemness_differentiation_rate * diff * stem * dt
        stem_new += cfg.stemness_plasticity_factor * plas_new * (1 - stem) * dt
        stem_new += cfg.stemness_stress_factor * stress_new * stem * dt
        stem_new = np.clip(stem_new, 0.0, 1.0)

        # 9. Differentiation
        # Increases with time, influenced by stemness threshold and plasticity
        diff_rate = cfg.differentiation_rate * (1 - diff) * dt
        # If stemness is low, differentiation accelerates
        diff_rate *= (1 + 2.0 * (1 - stem_new))
        # Plasticity allows dedifferentiation (reduce diff)
        dediff_rate = cfg.stemness_plasticity_factor * plas_new * diff * dt
        diff_new = diff + diff_rate - dediff_rate
        diff_new = np.clip(diff_new, 0.0, 1.0)

        # 10. Epigenetic age
        # Accumulates over time, reset partially by high plasticity
        age_new = age + cfg.age_accumulation_rate * dt
        age_new -= cfg.age_reset_fraction * plas_new * age_new * dt
        age_new = np.clip(age_new, 0.0, None)

        # Update state
        self.methylation = met_new
        self.acetylation = ace_new
        self.accessibility = acc_new
        self.expression = exp_new
        self.instability = inst_new
        self.plasticity = plas_new
        self.stemness = stem_new
        self.differentiation = diff_new
        self.stress = stress_new
        self.epigenetic_age = age_new

        # Update discrete states
        # Differentiation state
        self.diff_state = np.where(diff_new < 0.2, DifferentiationState.UNDIFFERENTIATED,
                                   np.where(diff_new < 0.5, DifferentiationState.PROGENITOR,
                                            np.where(diff_new < 0.8, DifferentiationState.DIFFERENTIATED,
                                                     DifferentiationState.TERMINALLY_DIFFERENTIATED)))

        # Chromatin state
        self.chromatin_state = np.where(acc_new < 0.3, ChromatinState.CLOSED,
                                        np.where(acc_new < 0.7, ChromatinState.INTERMEDIATE,
                                                 ChromatinState.OPEN))

        # Time update
        self._current_time += dt

    def record(self) -> None:
        """Record the current state into results."""
        res = self.results
        res.time.append(self._current_time)
        res.methylation_hist.append(self.methylation.copy())
        res.acetylation_hist.append(self.acetylation.copy())
        res.accessibility_hist.append(self.accessibility.copy())
        res.expression_hist.append(self.expression.copy())
        res.instability_hist.append(self.instability.copy())
        res.plasticity_hist.append(self.plasticity.copy())
        res.stemness_hist.append(self.stemness.copy())
        res.differentiation_hist.append(self.differentiation.copy())
        res.stress_hist.append(self.stress.copy())
        res.epigenetic_age_hist.append(self.epigenetic_age.copy())

        # Scalar metrics
        res.mean_methylation.append(np.mean(self.methylation))
        res.mean_acetylation.append(np.mean(self.acetylation))
        res.mean_accessibility.append(np.mean(self.accessibility))
        res.mean_expression.append(np.mean(self.expression))
        res.mean_instability.append(np.mean(self.instability))
        res.mean_plasticity.append(np.mean(self.plasticity))
        res.mean_stemness.append(np.mean(self.stemness))
        res.mean_differentiation.append(np.mean(self.differentiation))
        res.mean_stress.append(np.mean(self.stress))
        res.mean_epigenetic_age.append(np.mean(self.epigenetic_age))

    def validate_state(self) -> None:
        """Perform internal consistency checks."""
        n = self.cfg.num_regions
        for arr, name in [(self.methylation, "methylation"),
                          (self.acetylation, "acetylation"),
                          (self.accessibility, "accessibility"),
                          (self.expression, "expression"),
                          (self.instability, "instability"),
                          (self.plasticity, "plasticity"),
                          (self.stemness, "stemness"),
                          (self.differentiation, "differentiation"),
                          (self.stress, "stress"),
                          (self.epigenetic_age, "epigenetic_age")]:
            if arr.shape != (n,):
                raise RuntimeError(f"{name} array shape mismatch")
            if not np.all(np.isfinite(arr)):
                raise RuntimeError(f"{name} contains NaN or Inf")
            if np.any(arr < 0):
                raise RuntimeError(f"{name} contains negative values")
        # Bounds checks for variables expected in [0,1]
        for arr, name in [(self.methylation, "methylation"),
                          (self.acetylation, "acetylation"),
                          (self.accessibility, "accessibility"),
                          (self.stemness, "stemness"),
                          (self.differentiation, "differentiation")]:
            if np.any(arr > 1.0 + 1e-6):
                raise RuntimeError(f"{name} exceeds 1.0")
        # Discrete states valid
        if not np.all(np.isin(self.diff_state, [v.value for v in DifferentiationState])):
            raise RuntimeError("Invalid differentiation state values")
        if not np.all(np.isin(self.chromatin_state, [v.value for v in ChromatinState])):
            raise RuntimeError("Invalid chromatin state values")
        # History lengths
        n_steps = len(self.results.time)
        for hist in [self.results.methylation_hist, self.results.acetylation_hist,
                     self.results.accessibility_hist, self.results.expression_hist,
                     self.results.instability_hist, self.results.plasticity_hist,
                     self.results.stemness_hist, self.results.differentiation_hist,
                     self.results.stress_hist, self.results.epigenetic_age_hist]:
            if len(hist) != n_steps:
                raise RuntimeError("History length mismatch")

    # ----------------------------------------------------------------------
    # Public API for integration
    # ----------------------------------------------------------------------

    def get_region_methylation(self, region: int) -> float:
        if region < 0 or region >= self.cfg.num_regions:
            raise IndexError("Region index out of bounds")
        return float(self.methylation[region])

    def get_region_acetylation(self, region: int) -> float:
        if region < 0 or region >= self.cfg.num_regions:
            raise IndexError("Region index out of bounds")
        return float(self.acetylation[region])

    def get_region_accessibility(self, region: int) -> float:
        if region < 0 or region >= self.cfg.num_regions:
            raise IndexError("Region index out of bounds")
        return float(self.accessibility[region])

    def get_region_expression(self, region: int) -> float:
        if region < 0 or region >= self.cfg.num_regions:
            raise IndexError("Region index out of bounds")
        return float(self.expression[region])

    def get_region_stemness(self, region: int) -> float:
        if region < 0 or region >= self.cfg.num_regions:
            raise IndexError("Region index out of bounds")
        return float(self.stemness[region])

    def get_region_differentiation(self, region: int) -> float:
        if region < 0 or region >= self.cfg.num_regions:
            raise IndexError("Region index out of bounds")
        return float(self.differentiation[region])

    def get_average_epigenetic_fitness(self) -> float:
        """Compute a fitness-like metric based on expression and low instability."""
        avg_exp = np.mean(self.expression)
        avg_inst = np.mean(self.instability)
        return avg_exp / (1.0 + avg_inst)

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
        res.final_methylation = np.mean(self.methylation)
        res.final_acetylation = np.mean(self.acetylation)
        res.final_accessibility = np.mean(self.accessibility)
        res.final_expression = np.mean(self.expression)
        res.final_instability = np.mean(self.instability)
        res.final_plasticity = np.mean(self.plasticity)
        res.final_stemness = np.mean(self.stemness)
        res.final_differentiation = np.mean(self.differentiation)
        res.final_stress = np.mean(self.stress)
        res.final_epigenetic_age = np.mean(self.epigenetic_age)
        res.avg_fitness = self.get_average_epigenetic_fitness()

        # Distributions
        diff_counts = {int(v): 0 for v in DifferentiationState}
        for state in self.diff_state:
            diff_counts[int(state)] = diff_counts.get(int(state), 0) + 1
        res.differentiation_dist = diff_counts

        stemness_bins = np.linspace(0, 1, 5)
        stem_counts = {}
        for i in range(len(stemness_bins)-1):
            counts = np.sum((self.stemness >= stemness_bins[i]) & (self.stemness < stemness_bins[i+1]))
            stem_counts[f"{stemness_bins[i]:.1f}-{stemness_bins[i+1]:.1f}"] = int(counts)
        res.stemness_dist = stem_counts

        chrom_counts = {int(v): 0 for v in ChromatinState}
        for state in self.chromatin_state:
            chrom_counts[int(state)] = chrom_counts.get(int(state), 0) + 1
        res.chromatin_dist = chrom_counts

        return self.results


def print_summary(eng: EpigeneticsEngine, res: SimulationResults) -> None:
    """Print a comprehensive end‑of‑run summary."""
    print("=" * 60)
    print("Integrated Systems Oncology — Epigenetics Engine")
    print(f"Version: {ENGINE_VERSION}")
    print("=" * 60)
    print(f"Simulation mode: {'DEVELOPMENT' if eng.cfg.development_mode else 'PRODUCTION'}")
    print(f"Random seed: {eng.cfg.random_seed}")
    print(f"Time steps: {eng.cfg.time_steps}")
    print(f"Number of regions: {eng.cfg.num_regions}")
    print(f"Average methylation: {res.final_methylation:.4f}")
    print(f"Average acetylation: {res.final_acetylation:.4f}")
    print(f"Average chromatin accessibility: {res.final_accessibility:.4f}")
    print(f"Average gene expression potential: {res.final_expression:.4f}")
    print(f"Average instability: {res.final_instability:.4f}")
    print(f"Average plasticity: {res.final_plasticity:.4f}")
    print(f"Average stemness: {res.final_stemness:.4f}")
    print(f"Average differentiation: {res.final_differentiation:.4f}")
    print(f"Average stress: {res.final_stress:.4f}")
    print(f"Average epigenetic age: {res.final_epigenetic_age:.4f}")
    print(f"Average fitness score: {res.avg_fitness:.4f}")
    print("-" * 60)
    print("Differentiation state distribution:")
    for state, count in res.differentiation_dist.items():
        print(f"  {DifferentiationState(state).name}: {count}")
    print("Stemness distribution (binned):")
    for bin_range, count in res.stemness_dist.items():
        print(f"  {bin_range}: {count}")
    print("Chromatin state distribution:")
    for state, count in res.chromatin_dist.items():
        print(f"  {ChromatinState(state).name}: {count}")
    print("=" * 60)


def main() -> None:
    """Example usage of the Epigenetics Engine."""
    cfg = SimulationConfig()
    eng = EpigeneticsEngine(cfg)
    res = eng.run()
    print_summary(eng, res)


if __name__ == "__main__":
    main()