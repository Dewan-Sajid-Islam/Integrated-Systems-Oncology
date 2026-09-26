# Integrated Systems Oncology
## Parameter Reference Manual

**Repository Version 1.0.2**

This document lists the exact `SimulationConfig` fields and default values present in the current source code. These are implementation defaults, not empirically calibrated estimates or recommended biological ranges. Development-mode settings accelerate tests and should not be interpreted as research defaults.

# Tumor Evolution Engine

| Parameter | Default | Purpose |
|---|---:|---|
| `random_seed` | `42` | Seed used by NumPy random number generation. |
| `time_steps` | `10` | Number of discrete simulation steps. |
| `carrying_capacity` | `1000000.0` | Density-dependent population carrying capacity. |
| `initial_clone_count` | `3` | Number of founder clones. |
| `initial_population` | `1000.0` | Initial population assigned to each founder clone. |
| `mutation_rate` | `1e-06` | Base mutation probability per cell division. |
| `development_mode` | `True` | Enables accelerated/testing behavior. |
| `development_mutation_multiplier` | `150.0` | Multiplier applied to mutation attempts in development mode. |
| `lineage_establishment_probability` | `0.05` | Probability that a mutation attempt establishes a child lineage outside development mode. |
| `driver_mutation_probability` | `0.1` | Probability that a mutation attempt is classified as a driver. |
| `driver_effect_scale` | `0.1` | Standard deviation for driver phenotype effects. |
| `passenger_effect_scale` | `0.01` | Standard deviation for passenger phenotype effects. |
| `default_growth_rate` | `0.35` | Net baseline growth component used to derive the base birth rate. |
| `death_rate` | `0.01` | Base per-capita death rate. |
| `proliferation_base` | `1.0` | Initial proliferation-capacity setting. |
| `apoptosis_base` | `1.0` | Initial apoptosis-susceptibility setting. |
| `dna_repair_base` | `1.0` | Initial DNA repair efficiency setting. |
| `genomic_instability_base` | `0.0` | Initial genomic instability setting. |
| `metabolic_efficiency_base` | `1.0` | Initial metabolic-efficiency setting. |
| `immune_visibility_base` | `0.0` | Initial immune-visibility proxy setting. |
| `epigenetic_plasticity_base` | `0.0` | Initial epigenetic-plasticity trait. |
| `resistance_base` | `0.0` | Initial resistance-potential trait; not a therapy intervention model. |
| `strict_validation` | `True` | Enable engine state/invariant validation. |
| `extinction_threshold` | `1e-06` | Population threshold below which a clone is treated as extinct. |

# Metabolism Engine

| Parameter | Default | Purpose |
|---|---:|---|
| `random_seed` | `42` | Random seed for reproducibility. |
| `time_steps` | `100` | Number of simulation steps. |
| `dt` | `0.1` | Base integration time step. |
| `num_regions` | `10` | Number of spatial regions. |
| `vascular_density` | `0.3` | Fraction of regions designated as vascular. |
| `vascular_supply_oxygen` | `1.0` | Oxygen concentration imposed at vascular regions. |
| `vascular_supply_glucose` | `1.0` | Glucose concentration imposed at vascular regions. |
| `diffusion_oxygen` | `0.1` | Oxygen diffusion coefficient. |
| `diffusion_glucose` | `0.08` | Glucose diffusion coefficient. |
| `diffusion_lactate` | `0.05` | Lactate diffusion coefficient. |
| `diffusion_ph` | `0.02` | pH diffusion coefficient. |
| `oxygen_consumption_rate` | `0.05` | First-order oxygen consumption coefficient. |
| `glucose_consumption_rate` | `0.1` | First-order glucose consumption coefficient. |
| `glycolytic_atp_yield` | `2.0` | ATP yield factor for glycolysis. |
| `oxidative_atp_yield` | `36.0` | ATP yield factor for oxidative phosphorylation. |
| `lactate_production_rate` | `0.1` | Lactate production factor per glycolytic glucose use. |
| `warburg_bias` | `0.5` | Baseline glycolytic bias. |
| `aerobic_glycolysis_fraction` | `0.3` | Additional glycolytic fraction retained under oxygen-replete conditions. |
| `mitochondrial_efficiency_base` | `1.0` | Scaling factor for OXPHOS ATP production. |
| `initial_ph` | `7.4` | Initial / buffered pH baseline. |
| `ph_acidification_rate` | `0.05` | Lactate-driven pH acidification coefficient. |
| `ph_buffering` | `0.1` | Return-to-baseline pH buffering coefficient. |
| `ros_production_rate` | `0.02` | ROS production coefficient from OXPHOS ATP. |
| `ros_decay_rate` | `0.1` | First-order ROS decay coefficient. |
| `initial_ros` | `0.0` | Initial ROS level. |
| `necrosis_atp_threshold` | `0.2` | ATP threshold used with stress for necrosis triggering. |
| `necrosis_stress_threshold` | `0.8` | Stress threshold used with ATP for necrosis triggering. |
| `necrosis_duration_threshold` | `5` | Number of consecutive triggering steps required for necrosis. |
| `oxidative_oxygen_threshold` | `0.3` | Oxygen threshold for oxidative phenotype classification. |
| `hypoxic_oxygen_threshold` | `0.1` | Oxygen threshold for hypoxia. |
| `high_atp_threshold` | `0.6` | ATP threshold for high-ATP phenotype classification. |
| `low_atp_threshold` | `0.3` | ATP threshold for quiescent classification. |
| `development_mode` | `True` | Enable accelerated/testing time-step behavior. |
| `development_dt_multiplier` | `10.0` | Multiplier applied to `dt` in development mode. |
| `strict_validation` | `True` | Enable internal validation checks. |
| `initial_oxygen` | `0.8` | Initial oxygen concentration. |
| `initial_glucose` | `0.8` | Initial glucose concentration. |
| `initial_lactate` | `0.1` | Initial lactate concentration. |
| `initial_atp` | `1.0` | Initial ATP concentration. |

# Epigenetics Engine

| Parameter | Default | Purpose |
|---|---:|---|
| `random_seed` | `42` | Random seed for reproducibility. |
| `time_steps` | `100` | Number of simulation steps. |
| `dt` | `0.1` | Base integration time step. |
| `num_regions` | `10` | Number of spatial regions. |
| `methylation_drift_rate` | `0.01` | Rate of drift toward methylation equilibrium. |
| `methylation_equilibrium` | `0.5` | Target methylation equilibrium. |
| `demethylation_rate` | `0.02` | Active demethylation coefficient. |
| `methylation_stress_effect` | `0.05` | Stress-dependent methylation term. |
| `acetylation_rate` | `0.03` | Histone acetylation coefficient. |
| `deacetylation_rate` | `0.02` | Histone deacetylation coefficient. |
| `acetylation_equilibrium` | `0.5` | Target acetylation equilibrium. |
| `acetylation_stress_effect` | `0.04` | Stress-dependent acetylation term. |
| `accessibility_opening_rate` | `0.04` | Chromatin opening coefficient. |
| `accessibility_closing_rate` | `0.02` | Chromatin closing coefficient. |
| `accessibility_base` | `0.3` | Initial/base accessibility setting. |
| `expression_base` | `0.2` | Baseline gene-expression potential. |
| `expression_acetylation_factor` | `1.5` | Effect of acetylation on expression potential. |
| `expression_methylation_factor` | `-1.0` | Effect of methylation on expression potential (negative by default). |
| `expression_accessibility_factor` | `1.0` | Effect of accessibility on expression potential. |
| `expression_noise` | `0.02` | Standard deviation of expression noise. |
| `instability_base` | `0.05` | Baseline instability input per step. |
| `instability_stress_factor` | `1.5` | Stress contribution to instability. |
| `instability_decay` | `0.01` | Instability decay coefficient. |
| `plasticity_base` | `0.2` | Baseline plasticity input per step. |
| `plasticity_instability_factor` | `0.5` | Instability contribution to plasticity. |
| `plasticity_decay` | `0.01` | Plasticity decay coefficient. |
| `stemness_base` | `0.5` | Initial stemness. |
| `stemness_differentiation_rate` | `0.02` | Differentiation-driven stemness reduction. |
| `stemness_plasticity_factor` | `0.3` | Plasticity-driven stemness increase/dedifferentiation term. |
| `stemness_stress_factor` | `-0.2` | Stress contribution to stemness (negative by default). |
| `differentiation_rate` | `0.02` | Differentiation progression coefficient. |
| `differentiation_stemness_threshold` | `0.3` | Configured stemness threshold used by the model configuration. |
| `age_accumulation_rate` | `0.01` | Epigenetic-age accumulation coefficient. |
| `age_reset_fraction` | `0.1` | Plasticity-dependent age reset coefficient. |
| `stress_base` | `0.1` | Baseline stress input per step. |
| `stress_instability_factor` | `0.3` | Instability contribution to stress. |
| `stress_decay` | `0.02` | Stress decay coefficient. |
| `initial_methylation` | `0.5` | Initial methylation. |
| `initial_acetylation` | `0.5` | Initial acetylation. |
| `initial_accessibility` | `0.5` | Initial chromatin accessibility. |
| `initial_expression` | `0.5` | Initial expression potential. |
| `initial_instability` | `0.05` | Initial instability. |
| `initial_plasticity` | `0.2` | Initial plasticity state. |
| `initial_stemness` | `0.5` | Initial stemness state. |
| `initial_differentiation` | `0.0` | Initial differentiation. |
| `initial_stress` | `0.1` | Initial stress. |
| `initial_epigenetic_age` | `0.0` | Initial epigenetic age. |
| `strict_validation` | `True` | Enable internal validation checks. |
| `development_mode` | `True` | Enable accelerated/testing time-step behavior. |
| `development_dt_multiplier` | `10.0` | Multiplier applied to `dt` in development mode. |

# Synergy Engine

| Parameter | Default | Purpose |
|---|---:|---|
| `random_seed` | `42` | Random seed for reproducibility. |
| `time_steps` | `100` | Number of simulation steps. |
| `dt` | `0.1` | Base integration time step. |
| `num_regions` | `10` | Number of spatial regions. |
| `initial_tumor_fitness` | `0.5` | Initial tumor-fitness state. |
| `initial_metabolic_fitness` | `0.5` | Initial metabolic-fitness state. |
| `initial_epigenetic_fitness` | `0.5` | Initial epigenetic-fitness state. |
| `initial_stemness` | `0.5` | Initial stemness state. |
| `initial_plasticity` | `0.3` | Initial plasticity state. |
| `initial_mutation_pressure` | `0.1` | Initial mutation-pressure state. |
| `initial_selection_pressure` | `0.3` | Initial selection-pressure state. |
| `initial_metabolic_stress` | `0.1` | Initial metabolic stress state. |
| `initial_oxidative_stress` | `0.1` | Initial oxidative stress state. |
| `initial_hypoxia` | `0.1` | Initial hypoxia state. |
| `initial_chromatin_accessibility` | `0.5` | Initial chromatin-accessibility state. |
| `initial_gene_expression` | `0.5` | Initial gene-expression state. |
| `initial_adaptive_capacity` | `0.3` | Initial adaptive-capacity state. |
| `initial_therapy_resistance` | `0.1` | Initial therapy-resistance state. |
| `initial_cellular_resilience` | `0.4` | Initial cellular-resilience state. |
| `initial_system_stability` | `0.7` | Initial system-stability state. |
| `hypoxia_response_rate` | `0.2` | Hypoxia response coefficient. |
| `hypoxia_decay_rate` | `0.1` | Hypoxia decay coefficient. |
| `oxidative_stress_response_rate` | `0.15` | Oxidative-stress response coefficient. |
| `oxidative_stress_decay_rate` | `0.1` | Oxidative-stress decay coefficient. |
| `metabolic_stress_response_rate` | `0.2` | Metabolic-stress response coefficient. |
| `metabolic_stress_decay_rate` | `0.1` | Metabolic-stress decay coefficient. |
| `mutation_response_rate` | `0.15` | Mutation-pressure response coefficient. |
| `mutation_decay_rate` | `0.08` | Mutation-pressure decay coefficient. |
| `selection_response_rate` | `0.1` | Selection-pressure response coefficient. |
| `selection_decay_rate` | `0.08` | Selection-pressure decay coefficient. |
| `plasticity_response_rate` | `0.12` | Configured plasticity response coefficient (the current update uses the plasticity weight directly). |
| `plasticity_decay_rate` | `0.08` | Plasticity decay coefficient. |
| `resistance_response_rate` | `0.1` | Therapy-resistance response coefficient. |
| `resistance_decay_rate` | `0.06` | Therapy-resistance decay coefficient. |
| `chromatin_response_rate` | `0.1` | Chromatin-accessibility response coefficient. |
| `gene_expression_response_rate` | `0.12` | Configured gene-expression response parameter. |
| `adaptive_response_rate` | `0.1` | Configured adaptive-capacity response parameter. |
| `stemness_response_rate` | `0.12` | Configured stemness response parameter. |
| `resilience_response_rate` | `0.1` | Configured resilience response parameter. |
| `stability_response_rate` | `0.08` | Configured stability response parameter. |
| `hypoxia_metabolic_stress_weight` | `0.5` | Weight of hypoxia in metabolic stress. |
| `oxidative_stress_weight` | `0.5` | Weight of oxidative stress in metabolic stress. |
| `metabolic_stress_mutation_weight` | `0.6` | Weight of metabolic stress in mutation pressure. |
| `oxidative_stress_mutation_weight` | `0.4` | Weight of oxidative stress in mutation pressure. |
| `mutation_plasticity_weight` | `0.4` | Weight linking mutation pressure to plasticity. |
| `plasticity_resistance_weight` | `0.3` | Weight linking plasticity to resistance. |
| `chromatin_expression_weight` | `0.3` | Weight linking chromatin accessibility to gene expression. |
| `expression_adaptive_weight` | `0.3` | Weight linking gene expression to adaptive capacity. |
| `resilience_resistance_weight` | `0.2` | Weight linking resilience to resistance. |
| `stemness_resilience_weight` | `0.2` | Weight linking stemness and resilience. |
| `stability_resilience_weight` | `0.2` | Weight linking resilience to stability. |
| `resistance_fitness_cost` | `0.05` | Cost applied to tumor fitness from resistance. |
| `mutation_fitness_cost` | `0.05` | Cost applied to epigenetic fitness from mutation pressure. |
| `stress_stemness_reduction` | `0.03` | Stress-driven stemness reduction coefficient. |
| `stress_resilience_reduction` | `0.03` | Stress-driven resilience reduction coefficient. |
| `tumor_fitness_weight` | `0.4` | Weight of tumor fitness in combined fitness. |
| `metabolic_fitness_weight` | `0.3` | Weight of metabolic fitness in combined fitness. |
| `epigenetic_fitness_weight` | `0.3` | Weight of epigenetic fitness in combined fitness. |
| `heterogeneity_scale` | `0.05` | Scale of initial region-to-region heterogeneity. |
| `development_mode` | `True` | Enable accelerated/testing time-step behavior. |
| `development_dt_multiplier` | `10.0` | Multiplier applied to `dt` in development mode. |
| `strict_validation` | `True` | Enable internal validation checks. |

# Reproducibility Notes

All four engines initialize NumPy random-number generators with `numpy.random.default_rng(random_seed)`. For the same configuration and seed, recorded stochastic histories are reproducible on the same platform.

## Development mode

`development_mode` is intended for rapid testing. In the continuous engines it multiplies the effective time step by `development_dt_multiplier`; in Tumor Evolution it also increases mutation-attempt visibility and, for testing, raises the lineage-establishment probability to 0.3. Disable development mode for scientific runs unless you are explicitly studying its altered dynamics.

## Validation mode

`strict_validation = True` enables internal state checks. The validators test implementation-level invariants, numerical finiteness/bounds, expected directional behavior of implemented relationships, and reproducibility. They do not establish biological or clinical validity.

## Best practices

1. Record the exact ISO repository version and engine configuration used.
2. Record the random seed.
3. Keep `strict_validation` enabled for development and validation runs.
4. Use `validate_project.py` after source changes.
5. Save important simulation outputs and configuration values alongside analysis scripts.
