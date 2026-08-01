# Integrated Systems Oncology
## Parameter Reference Manual

**Version 1.0.0**

This document provides a comprehensive reference for every configurable parameter in the Integrated Systems Oncology (ISO) software suite. Each parameter has a clear biological interpretation, a typical range, and a description of its role in the simulation. By documenting all parameters, we ensure reproducibility, transparency, and ease of use for researchers, reviewers, and future developers.

All parameters are stored in the `SimulationConfig` dataclass of each engine. The framework is designed so that every parameter change corresponds to a specific biological assumption or experimental condition, enabling rigorous hypothesis testing and sensitivity analysis.

---

# Tumor Evolution Engine

| Parameter | Meaning | Typical Range | Biological Interpretation | Used For |
|-----------|---------|---------------|---------------------------|----------|
| `random_seed` | Seed for the NumPy random number generator | Any integer (e.g., 42) | Determines all stochastic events (mutations, birth, death) | Reproducibility |
| `time_steps` | Number of simulation steps | 10–1000 | Duration of simulated evolution | Simulation length |
| `carrying_capacity` | Maximum tumour cell population | 10³–10⁷ cells | Resource‑limited growth capacity | Logistic growth saturation |
| `initial_clone_count` | Number of clones at start | 1–10 | Initial clonal diversity | Starting population structure |
| `initial_population` | Population size per initial clone | 10–10⁵ cells | Founder population size | Starting tumour burden |
| `birth_rate` | Net per‑capita birth rate (base) | 0.1–1.0 | Intrinsic division rate | Cell proliferation |
| `death_rate` | Base per‑capita death rate | 0.01–0.1 | Baseline apoptosis/necrosis | Cell turnover |
| `mutation_rate` | Mutation probability per cell division | 10⁻⁹–10⁻⁵ | Genomic instability | Mutation frequency |
| `driver_mutation_probability` | Fraction of mutations that are driver | 0.01–0.3 | Proportion of non‑neutral mutations | Evolutionary selection |
| `lineage_establishment_probability` | Probability a new clone survives | 0.01–0.5 | Success rate of a new lineage | Clonal expansion |
| `fitness_advantage` | Growth rate effect of driver mutations | 0.01–0.2 | Selection coefficient | Fitness landscape |
| `development_mode` | Accelerates simulation for testing | True/False | Speeds up time steps | Debugging and validation |
| `strict_validation` | Enables internal consistency checks | True/False | Validates simulation invariants | Quality assurance |

---

# Metabolism Engine

| Parameter | Meaning | Typical Range | Biological Interpretation | Used For |
|-----------|---------|---------------|---------------------------|----------|
| `random_seed` | Seed for reproducibility | Any integer | All stochastic processes | Reproducibility |
| `time_steps` | Number of metabolic time steps | 50–500 | Simulation duration | Temporal resolution |
| `dt` | Time step size | 0.01–1.0 | Integration step | Numerical accuracy |
| `num_regions` | Number of spatial compartments | 5–50 | Spatial resolution | Gradient formation |
| `oxygen_supply` | Boundary oxygen concentration | 0.0–1.0 | Oxygen from vasculature | Tissue oxygenation |
| `glucose_supply` | Boundary glucose concentration | 0.0–1.0 | Glucose from vasculature | Nutrient supply |
| `diffusion_oxygen` | Oxygen diffusion coefficient | 0.01–0.5 | Tissue permeability | Gradient formation |
| `diffusion_glucose` | Glucose diffusion coefficient | 0.01–0.4 | Tissue permeability | Gradient formation |
| `diffusion_lactate` | Lactate diffusion coefficient | 0.01–0.3 | Waste removal | Acidosis spread |
| `diffusion_ph` | pH diffusion (buffering) | 0.001–0.1 | Proton mobility | pH equilibration |
| `vascular_density` | Fraction of regions with vessels | 0.05–0.5 | Angiogenesis | Nutrient delivery |
| `oxygen_consumption_rate` | Per‑capita oxygen uptake | 0.01–0.1 | Metabolic demand | OXPHOS activity |
| `glucose_consumption_rate` | Per‑capita glucose uptake | 0.02–0.2 | Glycolytic demand | Glycolysis |
| `warburg_bias` | Baseline glycolytic fraction | 0.0–1.0 | Aerobic glycolysis propensity | Phenotype bias |
| `glycolytic_atp_yield` | ATP per glucose via glycolysis | 2.0 (fixed) | ATP yield | Energy production |
| `oxidative_atp_yield` | ATP per glucose via OXPHOS | 36.0 (fixed) | ATP yield | Energy production |
| `mitochondrial_efficiency_base` | OXPHOS efficiency | 0.0–1.0 | Mitochondrial function | ATP production capacity |
| `hypoxia_threshold` | Oxygen below which hypoxia is triggered | 0.05–0.2 | Hypoxia sensing | Phenotype transition |
| `necrosis_atp_threshold` | ATP below which necrosis risk increases | 0.1–0.3 | Energy crisis | Cell death |
| `necrosis_stress_threshold` | Stress above which necrosis is accelerated | 0.5–0.9 | Stress accumulation | Necrotic transition |
| `necrosis_duration_threshold` | Number of steps with sustained stress before necrosis | 3–10 | Time threshold | Necrosis onset |
| `development_mode` | Speeds up simulation | True/False | Debugging | Validation |
| `strict_validation` | Enables internal checks | True/False | Quality assurance | Scientific integrity |

---

# Epigenetics Engine

| Parameter | Meaning | Typical Range | Biological Interpretation | Used For |
|-----------|---------|---------------|---------------------------|----------|
| `random_seed` | Seed for reproducibility | Any integer | All stochastic noise | Reproducibility |
| `time_steps` | Number of epigenetic time steps | 50–500 | Simulation length | Temporal dynamics |
| `dt` | Time step size | 0.01–1.0 | Integration step | Numerical stability |
| `num_regions` | Number of spatial regions | 5–50 | Spatial heterogeneity | Regional variation |
| `methylation_drift_rate` | Passive drift speed | 0.001–0.05 | Maintenance methylation | Baseline methylation |
| `demethylation_rate` | Active demethylation rate | 0.005–0.05 | TET‑mediated demethylation | Epigenetic reprogramming |
| `acetylation_rate` | Histone acetylation rate | 0.01–0.05 | HAT activity | Chromatin opening |
| `deacetylation_rate` | Histone deacetylation rate | 0.01–0.04 | HDAC activity | Chromatin closing |
| `accessibility_opening_rate` | Chromatin opening rate | 0.01–0.05 | Remodelling | Gene activation |
| `accessibility_closing_rate` | Chromatin closing rate | 0.005–0.03 | Remodelling | Gene silencing |
| `expression_noise` | Stochastic noise in gene expression | 0.0–0.05 | Transcriptional bursting | Variability |
| `instability_base` | Basal epigenetic instability | 0.01–0.1 | Stochastic variation | Plasticity |
| `plasticity_base` | Basal plasticity | 0.05–0.3 | Lineage flexibility | Differentiation potential |
| `stemness_base` | Basal stemness | 0.2–0.8 | Stem cell character | Differentiation state |
| `differentiation_rate` | Rate of differentiation | 0.01–0.05 | Commitment rate | Maturation |
| `age_accumulation_rate` | Epigenetic age increase | 0.005–0.02 | Epigenetic clock | Cellular age |
| `development_mode` | Accelerates simulation | True/False | Debugging | Validation |
| `strict_validation` | Enables internal checks | True/False | Quality assurance | Scientific integrity |

---

# Synergy Engine

| Parameter | Meaning | Typical Range | Biological Interpretation | Used For |
|-----------|---------|---------------|---------------------------|----------|
| `random_seed` | Seed for reproducibility | Any integer | Initial heterogeneity | Reproducibility |
| `time_steps` | Number of synergy time steps | 50–500 | Simulation length | System dynamics |
| `dt` | Time step size | 0.01–1.0 | Integration step | Numerical stability |
| `num_regions` | Number of spatial regions | 5–50 | Spatial heterogeneity | Regional interaction |
| `tumor_fitness_weight` | Weight of tumour fitness in combined fitness | 0.2–0.6 | Contribution of evolution | System fitness |
| `metabolic_fitness_weight` | Weight of metabolic fitness | 0.2–0.5 | Contribution of metabolism | System fitness |
| `epigenetic_fitness_weight` | Weight of epigenetic fitness | 0.2–0.5 | Contribution of epigenetics | System fitness |
| `hypoxia_metabolic_stress_weight` | Contribution of hypoxia to metabolic stress | 0.3–0.7 | Hypoxia impact | Stress generation |
| `oxidative_stress_weight` | Contribution of oxidative stress | 0.3–0.7 | ROS impact | Stress generation |
| `metabolic_stress_mutation_weight` | Stress effect on mutation pressure | 0.3–0.7 | Stress‑induced mutagenesis | Mutation rate |
| `mutation_plasticity_weight` | Mutation effect on plasticity | 0.2–0.5 | Genomic instability → plasticity | Adaptation |
| `plasticity_resistance_weight` | Plasticity effect on therapy resistance | 0.2–0.5 | Phenotypic plasticity → resistance | Therapy evasion |
| `chromatin_expression_weight` | Chromatin effect on gene expression | 0.2–0.5 | Epigenetic regulation | Gene activity |
| `expression_adaptive_weight` | Gene expression effect on adaptive capacity | 0.2–0.5 | Transcriptional adaptability | Evolution |
| `resilience_resistance_weight` | Resilience effect on therapy resistance | 0.1–0.4 | Cellular robustness → resistance | Therapy evasion |
| `stemness_resilience_weight` | Stemness effect on cellular resilience | 0.1–0.4 | Stem cell robustness | Resilience |
| `stability_resilience_weight` | Resilience effect on system stability | 0.1–0.4 | Robustness → stability | System integrity |
| `resistance_fitness_cost` | Fitness cost of therapy resistance | 0.01–0.1 | Trade‑off | Evolutionary cost |
| `mutation_fitness_cost` | Fitness cost of mutation pressure | 0.01–0.1 | Mutational load | Fitness reduction |
| `stress_stemness_reduction` | Stress‑induced stemness loss | 0.01–0.05 | Stress → differentiation | Stem cell depletion |
| `stress_resilience_reduction` | Stress‑induced resilience loss | 0.01–0.05 | Stress → fragility | Resilience loss |
| `development_mode` | Accelerates simulation | True/False | Debugging | Validation |
| `strict_validation` | Enables internal checks | True/False | Quality assurance | Scientific integrity |

---

# Random Seeds

The ISO framework is fully deterministic: given the same `random_seed` value, all stochastic processes produce identical sequences of random numbers. This is achieved using NumPy's `default_rng` with a seeded generator. This ensures that:

- Every simulation run can be exactly reproduced.
- Results are independent of system time or external factors.
- Sensitive analyses, such as parameter sweeps, can be performed reliably.
- Validation suites can verify reproducibility across runs.

Always report the `random_seed` used in your simulations. For production runs, choose a seed and document it alongside your parameter set.

---

# Development Mode

Development mode (`development_mode = True`) accelerates simulations by multiplying the time step (`dt`) by a configurable factor (`development_dt_multiplier`). This is intended for:

- Debugging the code and validating new features.
- Rapid testing of parameter ranges.
- Running validators that require many iterations.
- Early‑stage development.

**Important:** Development mode should **not** be used for biological experiments. It trades numerical accuracy for speed and may produce qualitatively different dynamics. Always disable development mode (`development_mode = False`) when performing research runs.

---

# Validation Mode

`strict_validation = True` enables a comprehensive suite of internal consistency checks at every time step. These checks include:

- Bounds checking (e.g., variables stay within [0,1]).
- Finite value checking (no NaN, no Inf).
- Shape and length consistency.
- Mass conservation (where applicable).
- Lineage acyclicity (Tumor Evolution Engine).
- Phenotype count sums (Metabolism Engine).
- Discrete state validity (Epigenetics Engine).

**When to enable:** Always enable `strict_validation` during development and validation runs. For performance‑critical production runs where you are confident of correctness, you may disable it to reduce runtime. However, we strongly recommend leaving it enabled for all scientific simulations.

---

# Best Practices

To ensure reproducibility and scientific rigor when using the ISO framework, we recommend the following practices:

1. **Document parameter changes** – Record every parameter value used in a simulation (including defaults). Use a version‑controlled parameter file or script.

2. **Never mix experimental and validation runs** – Always run validation on a separate seed and parameter set. Do not use the same seed for validation and experimentation.

3. **Always report the random seed** – Include the `random_seed` in all publications, reports, and supplementary materials.

4. **Archive simulation outputs** – Save the full `SimulationResults` object (or its key histories) for future analysis. Use a consistent naming convention.

5. **Validate before publishing** – Run `validate_project.py` on your working version to confirm that all engines pass their validation suites. This ensures that no accidental changes have broken the framework.

6. **Use stable Python and NumPy versions** – Record the versions used; future updates may affect reproducibility.

7. **Keep modules up‑to‑date** – Pull the latest bug fixes and improvements from the repository before starting new experiments.

8. **Write custom analysis scripts** – Use the public API (`get_region_*`, `get_average_*`, etc.) to extract data for custom figures and statistics, rather than parsing console output.

By following these guidelines, you will maximise the scientific value and reproducibility of your computational oncology research using Integrated Systems Oncology.