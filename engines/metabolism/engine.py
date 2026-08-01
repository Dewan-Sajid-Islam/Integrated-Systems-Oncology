# engine.py (corrected)
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Optional, List, Tuple, Dict
from enum import IntEnum
import math
import numpy as np

ENGINE_VERSION = "1.1.0"


class MetabolicPhenotype(IntEnum):
    """Metabolic phenotype classifications for each region."""
    OXIDATIVE = 0
    GLYCOLYTIC = 1
    INTERMEDIATE = 2
    HYPOXIC = 3
    QUIESCENT = 4
    NECROTIC = 5


@dataclass
class SimulationConfig:
    """Configuration parameters for the metabolic simulation."""

    # Core simulation parameters
    random_seed: int = 42
    time_steps: int = 100
    dt: float = 0.1
    num_regions: int = 10

    # Vascular supply (replaces single boundary)
    vascular_density: float = 0.3          # fraction of regions with vascular supply
    vascular_supply_oxygen: float = 1.0    # oxygen concentration from vessels
    vascular_supply_glucose: float = 1.0   # glucose concentration from vessels

    # Diffusion coefficients
    diffusion_oxygen: float = 0.1
    diffusion_glucose: float = 0.08
    diffusion_lactate: float = 0.05
    diffusion_ph: float = 0.02             # pH diffuses (buffering)

    # Cellular consumption parameters
    oxygen_consumption_rate: float = 0.05
    glucose_consumption_rate: float = 0.1

    # ATP yields
    glycolytic_atp_yield: float = 2.0
    oxidative_atp_yield: float = 36.0

    # Lactate production
    lactate_production_rate: float = 0.1

    # Warburg effect
    warburg_bias: float = 0.5              # 0 = no aerobic glycolysis, 1 = full Warburg
    aerobic_glycolysis_fraction: float = 0.3  # fraction of glucose glycolysed even with oxygen

    # Mitochondrial efficiency
    mitochondrial_efficiency_base: float = 1.0  # 0-1, scales OXPHOS

    # pH modelling
    initial_ph: float = 7.4
    ph_acidification_rate: float = 0.05    # pH drop per unit lactate
    ph_buffering: float = 0.1              # buffering capacity (restores pH towards neutral)

    # ROS modelling
    ros_production_rate: float = 0.02      # ROS per unit oxidative ATP
    ros_decay_rate: float = 0.1            # per time step
    initial_ros: float = 0.0

    # Necrosis
    necrosis_atp_threshold: float = 0.2    # below this ATP, necrosis risk
    necrosis_stress_threshold: float = 0.8
    necrosis_duration_threshold: int = 5   # steps of sustained stress before necrosis

    # Phenotype thresholds
    oxidative_oxygen_threshold: float = 0.3
    hypoxic_oxygen_threshold: float = 0.1
    high_atp_threshold: float = 0.6
    low_atp_threshold: float = 0.3

    # Development mode
    development_mode: bool = True
    development_dt_multiplier: float = 10.0

    # Validation
    strict_validation: bool = True

    # Initial conditions
    initial_oxygen: float = 0.8
    initial_glucose: float = 0.8
    initial_lactate: float = 0.1
    initial_atp: float = 1.0


@dataclass
class SimulationResults:
    """Container for all recorded simulation data."""
    time: List[float] = field(default_factory=list)

    # Spatial histories
    oxygen_hist: List[np.ndarray] = field(default_factory=list)
    glucose_hist: List[np.ndarray] = field(default_factory=list)
    lactate_hist: List[np.ndarray] = field(default_factory=list)
    atp_hist: List[np.ndarray] = field(default_factory=list)
    ph_hist: List[np.ndarray] = field(default_factory=list)
    ros_hist: List[np.ndarray] = field(default_factory=list)
    hypoxia_hist: List[np.ndarray] = field(default_factory=list)
    stress_hist: List[np.ndarray] = field(default_factory=list)
    necrosis_hist: List[np.ndarray] = field(default_factory=list)
    phenotype_hist: List[np.ndarray] = field(default_factory=list)

    # Scalar metrics per time step
    mean_atp: List[float] = field(default_factory=list)
    mean_oxygen: List[float] = field(default_factory=list)
    mean_glucose: List[float] = field(default_factory=list)
    mean_lactate: List[float] = field(default_factory=list)
    mean_ph: List[float] = field(default_factory=list)
    mean_ros: List[float] = field(default_factory=list)
    hypoxia_index: List[float] = field(default_factory=list)
    necrosis_fraction: List[float] = field(default_factory=list)
    metabolic_stress: List[float] = field(default_factory=list)

    # Phenotype distribution over time (counts per phenotype)
    phenotype_counts: List[Dict[int, int]] = field(default_factory=list)

    # Summary statistics (computed at end)
    final_oxygen: float = 0.0
    final_glucose: float = 0.0
    final_lactate: float = 0.0
    final_atp: float = 0.0
    final_ph: float = 0.0
    final_ros: float = 0.0
    max_atp: float = 0.0
    min_oxygen: float = 0.0
    max_lactate: float = 0.0
    min_ph: float = 0.0
    max_ros: float = 0.0
    avg_metabolic_fitness: float = 0.0
    final_necrosis_fraction: float = 0.0
    phenotype_distribution: Dict[int, int] = field(default_factory=dict)


class MetabolismEngine:
    """
    Metabolism Engine for the Integrated Systems Oncology framework.

    This engine models the spatiotemporal dynamics of key metabolites in a tumor
    microenvironment using a 1D diffusion-reaction model. It tracks oxygen,
    glucose, lactate, ATP, pH, ROS, and necrosis, with phenotypes and vascular supply.

    Version 1.1.0 adds:
      - Warburg effect with configurable bias.
      - Extracellular pH dynamics.
      - Metabolic phenotypes (oxidative, glycolytic, intermediate, hypoxic, quiescent, necrotic).
      - ATP as a driver of stress and phenotype.
      - Vascular supply map (replacing single boundary).
      - Mitochondrial efficiency.
      - ROS production and decay.
      - Necrosis when stress and ATP deficits persist.
      - Comprehensive public API for integration.
    """

    def __init__(self, cfg: SimulationConfig):
        self.cfg = cfg
        self.rng = np.random.default_rng(cfg.random_seed)
        self.results = SimulationResults()
        self._validate_config()

        n = cfg.num_regions
        self.oxygen: np.ndarray = np.zeros(n)
        self.glucose: np.ndarray = np.zeros(n)
        self.lactate: np.ndarray = np.zeros(n)
        self.atp: np.ndarray = np.zeros(n)
        self.ph: np.ndarray = np.zeros(n)
        self.ros: np.ndarray = np.zeros(n)

        # Derived metrics
        self.hypoxia: np.ndarray = np.zeros(n, dtype=bool)
        self.stress: np.ndarray = np.zeros(n)
        self.necrotic: np.ndarray = np.zeros(n, dtype=bool)
        self.phenotype: np.ndarray = np.full(n, MetabolicPhenotype.INTERMEDIATE, dtype=np.int8)

        # Vascular supply map (per region)
        self.vascular_supply: np.ndarray = np.zeros(n)

        # Necrosis timer (steps of stress above threshold)
        self._necrosis_timer: np.ndarray = np.zeros(n, dtype=int)

        # Time tracking
        self._current_time: float = 0.0
        self._build_vascular_map()

    def _validate_config(self) -> None:
        cfg = self.cfg
        if cfg.time_steps < 1:
            raise ValueError("time_steps must be at least 1")
        if cfg.dt <= 0:
            raise ValueError("dt must be positive")
        if cfg.num_regions < 1:
            raise ValueError("num_regions must be at least 1")
        if cfg.vascular_density < 0 or cfg.vascular_density > 1:
            raise ValueError("vascular_density must be between 0 and 1")
        if cfg.vascular_supply_oxygen < 0 or cfg.vascular_supply_glucose < 0:
            raise ValueError("vascular supply concentrations must be non-negative")
        if cfg.diffusion_oxygen < 0 or cfg.diffusion_glucose < 0 or cfg.diffusion_lactate < 0 or cfg.diffusion_ph < 0:
            raise ValueError("diffusion coefficients must be non-negative")
        if cfg.oxygen_consumption_rate < 0 or cfg.glucose_consumption_rate < 0:
            raise ValueError("consumption rates must be non-negative")
        if cfg.glycolytic_atp_yield < 0 or cfg.oxidative_atp_yield < 0:
            raise ValueError("ATP yields must be non-negative")
        if cfg.lactate_production_rate < 0:
            raise ValueError("lactate production rate must be non-negative")
        if cfg.warburg_bias < 0 or cfg.warburg_bias > 1:
            raise ValueError("warburg_bias must be between 0 and 1")
        if cfg.aerobic_glycolysis_fraction < 0 or cfg.aerobic_glycolysis_fraction > 1:
            raise ValueError("aerobic_glycolysis_fraction must be between 0 and 1")
        if not (0 <= cfg.mitochondrial_efficiency_base <= 1):
            raise ValueError("mitochondrial_efficiency_base must be between 0 and 1")
        if cfg.ph_acidification_rate < 0:
            raise ValueError("ph_acidification_rate must be non-negative")
        if cfg.ros_production_rate < 0 or cfg.ros_decay_rate < 0:
            raise ValueError("ROS rates must be non-negative")
        if cfg.necrosis_atp_threshold < 0 or cfg.necrosis_stress_threshold < 0:
            raise ValueError("necrosis thresholds must be non-negative")
        if cfg.necrosis_duration_threshold < 1:
            raise ValueError("necrosis_duration_threshold must be at least 1")
        if cfg.initial_oxygen < 0 or cfg.initial_glucose < 0 or cfg.initial_lactate < 0 or cfg.initial_atp < 0:
            raise ValueError("initial concentrations must be non-negative")
        if cfg.initial_ph < 0 or cfg.initial_ph > 14:
            raise ValueError("initial_ph must be between 0 and 14")
        if cfg.initial_ros < 0:
            raise ValueError("initial_ros must be non-negative")

    def _build_vascular_map(self) -> None:
        """Create a vascular supply map: regions with vessels supply nutrients."""
        n = self.cfg.num_regions
        # Randomly assign vascular regions based on vascular_density, but keep deterministic via seed.
        # Use the RNG to generate a binary mask.
        vascular = self.rng.random(n) < self.cfg.vascular_density
        # Ensure at least one vascular region.
        if not np.any(vascular):
            vascular[0] = True
        self.vascular_supply = vascular.astype(float)
        # Set supply concentration in vascular regions.
        self.vascular_supply *= self.cfg.vascular_supply_oxygen  # will be used for oxygen and glucose
        # We'll store a separate glucose supply, but we can reuse the same mask.
        # We'll store both supply values in separate arrays for clarity.
        self._vascular_oxygen_supply = self.vascular_supply * self.cfg.vascular_supply_oxygen
        self._vascular_glucose_supply = self.vascular_supply * self.cfg.vascular_supply_glucose

    def initialize_state(self) -> None:
        """Set initial concentrations and reset results."""
        n = self.cfg.num_regions
        self.oxygen.fill(self.cfg.initial_oxygen)
        self.glucose.fill(self.cfg.initial_glucose)
        self.lactate.fill(self.cfg.initial_lactate)
        self.atp.fill(self.cfg.initial_atp)
        self.ph.fill(self.cfg.initial_ph)
        self.ros.fill(self.cfg.initial_ros)
        self.hypoxia.fill(False)
        self.stress.fill(0.0)
        self.necrotic.fill(False)
        self.phenotype.fill(MetabolicPhenotype.INTERMEDIATE)
        self._necrosis_timer.fill(0)
        self._current_time = 0.0
        self.results = SimulationResults()

    def _compute_diffusion(self, concentration: np.ndarray, diff_coeff: float) -> np.ndarray:
        """
        Compute diffusion flux using central differences with zero‑flux boundaries
        except for vascular regions that are fixed to supply.
        """
        n = len(concentration)
        flux = np.zeros(n)
        if n <= 2:
            return flux
        # Internal nodes
        for i in range(1, n-1):
            flux[i] = diff_coeff * (concentration[i-1] - 2*concentration[i] + concentration[i+1])
        # Boundaries: zero-flux at both ends (vascular regions are handled by boundary condition after update)
        flux[0] = diff_coeff * (concentration[1] - concentration[0])
        flux[n-1] = diff_coeff * (concentration[n-2] - concentration[n-1])
        return flux

    def _step(self) -> None:
        cfg = self.cfg
        dt = cfg.dt
        if cfg.development_mode:
            dt *= cfg.development_dt_multiplier

        O2 = self.oxygen
        Glu = self.glucose
        Lac = self.lactate
        ATP = self.atp
        pH = self.ph
        ROS = self.ros
        nec = self.necrotic

        # 1. Compute consumption and production per region, accounting for necrosis (no activity)
        # For necrotic regions, set consumption to zero, and set metabolite changes to decay only.
        # We'll compute rates first, then apply to non-necrotic only.

        # Oxygen consumption: first-order
        o2_consumed = np.zeros_like(O2)
        glu_consumed = np.zeros_like(Glu)
        lactate_produced = np.zeros_like(Lac)
        atp_produced = np.zeros_like(ATP)
        ros_produced = np.zeros_like(ROS)

        # For non-necrotic regions
        alive = ~nec
        O2_alive = O2[alive]
        Glu_alive = Glu[alive]
        ATP_alive = ATP[alive]

        # Determine Warburg factor: even with oxygen, a fraction of glucose is glycolysed.
        # warburg_bias determines the baseline glycolytic fraction; aerobic_glycolysis_fraction adds a constant.
        # We'll compute glycolytic_fraction = warburg_bias + (1 - warburg_bias) * (1 - oxygen_norm)
        # where oxygen_norm is clamped to [0,1].
        o2_norm = np.clip(O2_alive / 1.0, 0.0, 1.0)
        glycolytic_fraction = cfg.warburg_bias + (1 - cfg.warburg_bias) * (1 - o2_norm)
        # Add aerobic glycolysis fraction (constant)
        glycolytic_fraction = np.clip(glycolytic_fraction + cfg.aerobic_glycolysis_fraction, 0.0, 1.0)

        # Consumption rates
        # Oxygen consumption: proportional to oxygen and (1 - glycolytic_fraction) because less oxygen used if glycolytic
        o2_consumed_alive = cfg.oxygen_consumption_rate * O2_alive * (1 - glycolytic_fraction) * dt
        # Glucose consumption: proportional to glucose, and increased by glycolytic fraction
        glu_consumed_alive = cfg.glucose_consumption_rate * Glu_alive * (1 + glycolytic_fraction) * dt

        # ATP production
        # From glycolysis: fraction of glucose that goes glycolytic
        atp_glycolysis = glu_consumed_alive * glycolytic_fraction * cfg.glycolytic_atp_yield
        # From OXPHOS: fraction that goes oxidative, scaled by mitochondrial efficiency
        oxidative_fraction = 1 - glycolytic_fraction
        mito_eff = cfg.mitochondrial_efficiency_base
        atp_oxphos = glu_consumed_alive * oxidative_fraction * cfg.oxidative_atp_yield * mito_eff

        atp_produced_alive = atp_glycolysis + atp_oxphos

        # Lactate production: from glycolysis (per glucose glycolysed)
        lactate_produced_alive = glu_consumed_alive * glycolytic_fraction * cfg.lactate_production_rate

        # ROS production: proportional to oxidative ATP production
        ros_produced_alive = cfg.ros_production_rate * atp_oxphos

        # Assign to arrays
        o2_consumed[alive] = o2_consumed_alive
        glu_consumed[alive] = glu_consumed_alive
        lactate_produced[alive] = lactate_produced_alive
        atp_produced[alive] = atp_produced_alive
        ros_produced[alive] = ros_produced_alive

        # 2. Update concentrations with diffusion
        O2_new = O2 - o2_consumed + self._compute_diffusion(O2, cfg.diffusion_oxygen) * dt
        Glu_new = Glu - glu_consumed + self._compute_diffusion(Glu, cfg.diffusion_glucose) * dt
        Lac_new = Lac + lactate_produced + self._compute_diffusion(Lac, cfg.diffusion_lactate) * dt
        ATP_new = ATP + atp_produced - 0.1 * ATP * dt  # basal ATP consumption

        # pH: lactate acidifies, and there is buffering towards initial pH.
        # pH change = - acidification_rate * lactate + buffering * (initial_ph - pH)
        ph_change = -cfg.ph_acidification_rate * Lac * dt + cfg.ph_buffering * (cfg.initial_ph - pH) * dt
        pH_new = pH + ph_change + self._compute_diffusion(pH, cfg.diffusion_ph) * dt

        # ROS: production + decay
        ROS_new = ROS + ros_produced - cfg.ros_decay_rate * ROS * dt + self._compute_diffusion(ROS, 0.02) * dt

        # Apply vascular supply: regions with vessels get nutrients (fixed concentration)
        # We set vascular regions to supply concentration, overriding diffusion.
        O2_new[self.vascular_supply > 0] = self.cfg.vascular_supply_oxygen
        Glu_new[self.vascular_supply > 0] = self.cfg.vascular_supply_glucose

        # Necrotic regions: set all metabolites to zero or low, and no consumption
        O2_new[nec] = 0.0
        Glu_new[nec] = 0.0
        Lac_new[nec] = 0.0
        ATP_new[nec] = 0.0
        pH_new[nec] = cfg.initial_ph  # pH returns to neutral in dead tissue
        ROS_new[nec] = 0.0

        # 3. Enforce non‑negativity and caps
        O2_new = np.maximum(O2_new, 0.0)
        Glu_new = np.maximum(Glu_new, 0.0)
        Lac_new = np.maximum(Lac_new, 0.0)
        ATP_new = np.maximum(ATP_new, 0.0)
        pH_new = np.clip(pH_new, 0.0, 14.0)
        ROS_new = np.maximum(ROS_new, 0.0)

        # 4. Update state
        self.oxygen = O2_new
        self.glucose = Glu_new
        self.lactate = Lac_new
        self.atp = ATP_new
        self.ph = pH_new
        self.ros = ROS_new

        # 5. Compute derived metrics
        self.hypoxia = (self.oxygen < cfg.hypoxic_oxygen_threshold) & ~nec
        # Metabolic stress: combination of ATP deficit and lactate/acidosis
        # Guard against division by zero if initial_atp is zero.
        if cfg.initial_atp <= 0:
            atp_deficit = np.zeros_like(ATP_new)
        else:
            atp_deficit = np.maximum(0.0, 1.0 - ATP_new / cfg.initial_atp)
        lactate_stress = np.clip(Lac_new / 0.5, 0.0, 1.0)
        ph_stress = np.clip((7.4 - pH_new) / 1.0, 0.0, 1.0)  # pH below 6.4 is extreme
        self.stress = 0.4 * atp_deficit + 0.3 * lactate_stress + 0.3 * ph_stress

        # 6. Determine phenotypes and necrosis
        # Necrosis: if stress > threshold and ATP < threshold for N steps
        stress_high = self.stress > cfg.necrosis_stress_threshold
        atp_low = ATP_new < cfg.necrosis_atp_threshold
        nec_trigger = stress_high & atp_low
        self._necrosis_timer = np.where(nec_trigger, self._necrosis_timer + 1, 0)
        new_necrosis = self._necrosis_timer >= cfg.necrosis_duration_threshold
        # Only mark non-necrotic regions as necrotic; necrotic stays necrotic.
        self.necrotic = self.necrotic | new_necrosis

        # Update phenotype for alive regions
        for i in range(self.cfg.num_regions):
            if self.necrotic[i]:
                self.phenotype[i] = MetabolicPhenotype.NECROTIC
            else:
                o2 = O2_new[i]
                atp_val = ATP_new[i]
                if o2 > cfg.oxidative_oxygen_threshold and atp_val > cfg.high_atp_threshold:
                    self.phenotype[i] = MetabolicPhenotype.OXIDATIVE
                elif o2 < cfg.hypoxic_oxygen_threshold:
                    self.phenotype[i] = MetabolicPhenotype.HYPOXIC
                elif atp_val < cfg.low_atp_threshold:
                    self.phenotype[i] = MetabolicPhenotype.QUIESCENT
                else:
                    # Determine glycolytic vs intermediate based on lactate or stress
                    if self.stress[i] > 0.3:
                        self.phenotype[i] = MetabolicPhenotype.GLYCOLYTIC
                    else:
                        self.phenotype[i] = MetabolicPhenotype.INTERMEDIATE

        # Update time
        self._current_time += dt

    def record(self) -> None:
        """Record the current state into results."""
        res = self.results
        res.time.append(self._current_time)
        res.oxygen_hist.append(self.oxygen.copy())
        res.glucose_hist.append(self.glucose.copy())
        res.lactate_hist.append(self.lactate.copy())
        res.atp_hist.append(self.atp.copy())
        res.ph_hist.append(self.ph.copy())
        res.ros_hist.append(self.ros.copy())
        res.hypoxia_hist.append(self.hypoxia.copy())
        res.stress_hist.append(self.stress.copy())
        res.necrosis_hist.append(self.necrotic.copy())
        res.phenotype_hist.append(self.phenotype.copy())

        # Scalar metrics
        res.mean_atp.append(np.mean(self.atp))
        res.mean_oxygen.append(np.mean(self.oxygen))
        res.mean_glucose.append(np.mean(self.glucose))
        res.mean_lactate.append(np.mean(self.lactate))
        res.mean_ph.append(np.mean(self.ph))
        res.mean_ros.append(np.mean(self.ros))
        res.hypoxia_index.append(np.mean(self.hypoxia))
        res.necrosis_fraction.append(np.mean(self.necrotic))
        res.metabolic_stress.append(np.mean(self.stress))

        # Phenotype counts
        counts = {int(p): 0 for p in MetabolicPhenotype}
        for phen in self.phenotype:
            counts[int(phen)] = counts.get(int(phen), 0) + 1
        res.phenotype_counts.append(counts)

    def validate_state(self) -> None:
        """Perform internal consistency checks."""
        cfg = self.cfg
        n = cfg.num_regions
        for arr, name in [(self.oxygen, "oxygen"), (self.glucose, "glucose"),
                          (self.lactate, "lactate"), (self.atp, "ATP"),
                          (self.ph, "pH"), (self.ros, "ROS")]:
            if arr.shape != (n,):
                raise RuntimeError(f"{name} array shape mismatch")
            if not np.all(np.isfinite(arr)):
                raise RuntimeError(f"{name} contains NaN or Inf")
            if np.any(arr < 0):
                raise RuntimeError(f"{name} contains negative values")
        # pH range
        if np.any(self.ph < 0) or np.any(self.ph > 14):
            raise RuntimeError("pH out of valid range (0-14)")
        # ROS non-negative
        if np.any(self.ros < 0):
            raise RuntimeError("ROS negative")
        # Necrotic flag consistency: necrotic regions have zero metabolites
        if np.any(self.necrotic & (self.oxygen > 1e-6)):
            raise RuntimeError("Necrotic region has non-zero oxygen")
        if np.any(self.necrotic & (self.glucose > 1e-6)):
            raise RuntimeError("Necrotic region has non-zero glucose")
        if np.any(self.necrotic & (self.lactate > 1e-6)):
            raise RuntimeError("Necrotic region has non-zero lactate")
        if np.any(self.necrotic & (self.atp > 1e-6)):
            raise RuntimeError("Necrotic region has non-zero ATP")
        # Vascular supply consistency: check that vascular regions have supply
        # (already enforced in step)
        # Check history lengths
        n_steps = len(self.results.time)
        for hist in [self.results.oxygen_hist, self.results.glucose_hist,
                     self.results.lactate_hist, self.results.atp_hist,
                     self.results.ph_hist, self.results.ros_hist,
                     self.results.hypoxia_hist, self.results.stress_hist,
                     self.results.necrosis_hist, self.results.phenotype_hist]:
            if len(hist) != n_steps:
                raise RuntimeError("History length mismatch")
        # Phenotype counts consistent
        for counts in self.results.phenotype_counts:
            if sum(counts.values()) != n:
                raise RuntimeError("Phenotype counts sum mismatch")

    # ----------------------------------------------------------------------
    # Public API for integration with other engines
    # ----------------------------------------------------------------------

    def get_average_atp(self) -> float:
        return float(np.mean(self.atp))

    def get_region_atp(self, region: int) -> float:
        if region < 0 or region >= self.cfg.num_regions:
            raise IndexError("Region index out of bounds")
        return float(self.atp[region])

    def get_region_oxygen(self, region: int) -> float:
        if region < 0 or region >= self.cfg.num_regions:
            raise IndexError("Region index out of bounds")
        return float(self.oxygen[region])

    def get_region_glucose(self, region: int) -> float:
        if region < 0 or region >= self.cfg.num_regions:
            raise IndexError("Region index out of bounds")
        return float(self.glucose[region])

    def get_region_lactate(self, region: int) -> float:
        if region < 0 or region >= self.cfg.num_regions:
            raise IndexError("Region index out of bounds")
        return float(self.lactate[region])

    def get_region_ph(self, region: int) -> float:
        if region < 0 or region >= self.cfg.num_regions:
            raise IndexError("Region index out of bounds")
        return float(self.ph[region])

    def get_region_ros(self, region: int) -> float:
        if region < 0 or region >= self.cfg.num_regions:
            raise IndexError("Region index out of bounds")
        return float(self.ros[region])

    def get_metabolic_fitness(self) -> float:
        """Return a scalar fitness score: high ATP and low stress."""
        avg_atp = np.mean(self.atp)
        avg_stress = np.mean(self.stress)
        if avg_stress > 1e-6:
            return avg_atp / (1.0 + avg_stress)
        return avg_atp

    def get_hypoxia_index(self) -> float:
        return float(np.mean(self.hypoxia))

    def get_necrosis_fraction(self) -> float:
        return float(np.mean(self.necrotic))

    def get_phenotype_distribution(self) -> Dict[int, int]:
        counts = {int(p): 0 for p in MetabolicPhenotype}
        for phen in self.phenotype:
            counts[int(phen)] = counts.get(int(phen), 0) + 1
        return counts

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
        res.final_oxygen = np.mean(self.oxygen)
        res.final_glucose = np.mean(self.glucose)
        res.final_lactate = np.mean(self.lactate)
        res.final_atp = np.mean(self.atp)
        res.final_ph = np.mean(self.ph)
        res.final_ros = np.mean(self.ros)
        res.max_atp = max(res.mean_atp) if res.mean_atp else 0.0
        res.min_oxygen = min(res.mean_oxygen) if res.mean_oxygen else 0.0
        res.max_lactate = max(res.mean_lactate) if res.mean_lactate else 0.0
        res.min_ph = min(res.mean_ph) if res.mean_ph else 0.0
        res.max_ros = max(res.mean_ros) if res.mean_ros else 0.0
        res.final_necrosis_fraction = np.mean(self.necrotic)
        res.phenotype_distribution = self.get_phenotype_distribution()
        res.avg_metabolic_fitness = self.get_metabolic_fitness()

        return self.results


def print_summary(eng: MetabolismEngine, res: SimulationResults) -> None:
    """Print a comprehensive end‑of‑run summary."""
    print("=" * 60)
    print("Integrated Systems Oncology — Metabolism Engine")
    print(f"Version: {ENGINE_VERSION}")
    print("=" * 60)
    print(f"Simulation mode: {'DEVELOPMENT' if eng.cfg.development_mode else 'PRODUCTION'}")
    print(f"Random seed: {eng.cfg.random_seed}")
    print(f"Time steps: {eng.cfg.time_steps}")
    print(f"Number of regions: {eng.cfg.num_regions}")
    print(f"Final ATP: {res.final_atp:.4f} (peak: {res.max_atp:.4f})")
    print(f"Final oxygen: {res.final_oxygen:.4f} (min: {res.min_oxygen:.4f})")
    print(f"Final glucose: {res.final_glucose:.4f}")
    print(f"Final lactate: {res.final_lactate:.4f} (max: {res.max_lactate:.4f})")
    print(f"Final pH: {res.final_ph:.4f} (min: {res.min_ph:.4f})")
    print(f"Final ROS: {res.final_ros:.4f} (max: {res.max_ros:.4f})")
    print(f"Hypoxia index (final): {res.hypoxia_index[-1] if res.hypoxia_index else 0.0:.4f}")
    print(f"Necrosis fraction (final): {res.final_necrosis_fraction:.4f}")
    print(f"Metabolic stress (final): {res.metabolic_stress[-1] if res.metabolic_stress else 0.0:.4f}")
    print(f"Average metabolic fitness: {res.avg_metabolic_fitness:.4f}")
    print("-" * 60)
    print("Spatial profiles at final time:")
    print(f"  Oxygen: min={eng.oxygen.min():.4f}, max={eng.oxygen.max():.4f}, mean={eng.oxygen.mean():.4f}")
    print(f"  Glucose: min={eng.glucose.min():.4f}, max={eng.glucose.max():.4f}, mean={eng.glucose.mean():.4f}")
    print(f"  Lactate: min={eng.lactate.min():.4f}, max={eng.lactate.max():.4f}, mean={eng.lactate.mean():.4f}")
    print(f"  ATP: min={eng.atp.min():.4f}, max={eng.atp.max():.4f}, mean={eng.atp.mean():.4f}")
    print(f"  pH: min={eng.ph.min():.4f}, max={eng.ph.max():.4f}, mean={eng.ph.mean():.4f}")
    print(f"  ROS: min={eng.ros.min():.4f}, max={eng.ros.max():.4f}, mean={eng.ros.mean():.4f}")
    print("-" * 60)
    print("Phenotype distribution (counts):")
    dist = res.phenotype_distribution
    for phen in MetabolicPhenotype:
        print(f"  {phen.name}: {dist.get(phen, 0)}")
    print("=" * 60)


def main() -> None:
    """Example usage of the Metabolism Engine."""
    cfg = SimulationConfig()
    eng = MetabolismEngine(cfg)
    res = eng.run()
    print_summary(eng, res)


if __name__ == "__main__":
    main()