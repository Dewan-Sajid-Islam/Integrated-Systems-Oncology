# Integrated Systems Oncology
## Software Architecture

**Repository Version 1.0.2**

This document describes the implemented software architecture of the Integrated Systems Oncology (ISO) framework. It covers module responsibilities, process execution, data flow, validation, and extension points. The architecture is modular and designed for transparent computational experimentation.

---

# High-Level Architecture

The ISO framework is composed of four independent simulation engines. A master script launches them sequentially as separate subprocesses, and a project-wide validator launches their validation suites. The engines do not import one another, and the current master script does not transfer live state trajectories between engines at each simulation step.

```text
┌─────────────────────────────────────────────────────────────┐
│                     Master Engine                           │
│                 (master_engine.py)                          │
│          sequential subprocess orchestration                │
└─────────────────────────────────────────────────────────────┘
                           │
        ┌──────────────────┼──────────────────┐
        ▼                  ▼                  ▼
  Tumor Evolution     Metabolism        Epigenetics
        │                  │                  │
        └──────────────────┴──────────────────┘
                           │
                           ▼
                       Synergy
```

The diagram represents execution order and architectural grouping, not automatic live state transfer among engines.

---

# Module Responsibilities

## Tumor Evolution Engine

**Inputs:** `SimulationConfig` (seed, carrying capacity, initial clone settings, mutation settings, phenotype modifiers, validation options)

**Outputs:** `SimulationResults` (tumor burden, clone populations/frequencies, diversity, mutation records, clone fitness, lineage information, extinction statistics)

**Responsibilities:**
- Density-dependent stochastic birth and death processes.
- Mutation opportunity generation from births.
- Driver/passenger classification and probabilistic lineage establishment.
- Heritable phenotype modification and lineage tracking.
- Shannon and Simpson diversity metrics.
- Derived fitness (`birth rate - death rate`).
- Seeded NumPy random number generation.

**Selection note:** there is no explicit replicator-dynamics population-rescaling operator. Differential effective birth and death rates produce differential expansion and therefore emergent selection.

**Public API:** `run()`, `initialize_population()`, `shannon()`, `simpson()`, `get_clone_frequencies()`, `get_lineage_summary()`.

---

## Metabolism Engine

**Inputs:** `SimulationConfig` (diffusion coefficients, supplies, consumption/production rates, phenotype thresholds, development and validation options)

**Outputs:** `SimulationResults` (oxygen, glucose, lactate, ATP, pH, ROS, hypoxia, stress, necrosis, phenotype histories)

**Responsibilities:**
- 1D diffusion-reaction-style update of metabolic fields.
- Oxygen and glucose consumption.
- Glycolytic and oxidative ATP production.
- Warburg bias and aerobic glycolysis.
- Lactate, ROS, and pH dynamics.
- Vascular supply constraints.
- Hypoxia, stress, necrosis, and discrete metabolic phenotype assignment.

**Numerical treatment:** explicit time-stepping; `development_mode` multiplies the effective time step by `development_dt_multiplier`.

---

## Epigenetics Engine

**Inputs:** `SimulationConfig` (chromatin rates, stress factors, plasticity/stemness parameters, initial states, validation options)

**Outputs:** `SimulationResults` (methylation, acetylation, accessibility, expression, instability, plasticity, stemness, differentiation, stress, age, discrete state classifications)

**Responsibilities:**
- Dynamic DNA methylation and histone acetylation.
- Chromatin accessibility dynamics.
- Gene-expression potential with stochastic noise.
- Epigenetic instability and plasticity.
- Stemness/differentiation dynamics and discrete state classification.
- Epigenetic age accumulation and partial reset.

**Numerical treatment:** explicit Euler-style time-stepping of the continuous state variables.

---

## Synergy Engine

**Inputs:** `SimulationConfig` containing initial subsystem fitness/state values, feedback coefficients, fitness weights, seed, and validation options.

**Outputs:** `SimulationResults` containing combined fitness, mutation pressure, selection pressure, stresses, therapy resistance, adaptive capacity, cellular resilience, and system stability.

**Responsibilities:**
- Weighted aggregation of tumor, metabolic, and epigenetic fitness.
- Bounded feedback dynamics among modeled state variables.
- Mutation pressure, resistance, adaptive capacity, resilience, and stability dynamics.
- Seeded reproducibility and state validation.

**Coupling note:** in the current release the Synergy Engine has its own initialized state and does not consume live trajectories produced by the preceding engine processes. The interaction is therefore model-level rather than a step-synchronized multi-engine simulation.

---

# Master Engine

`master_engine.py` orchestrates execution of all four engines.

**Purpose:** provide one command for sequential framework execution.

**Execution order:**
1. Tumor Evolution
2. Metabolism
3. Epigenetics
4. Synergy

**Failure handling:** if one engine exits with a non-zero code, the master continues to the remaining engines and reports the failure in its summary.

**Timing:** each subprocess is timed and displayed.

**Process isolation:** engines run as separate Python subprocesses in their own directories.

**State transfer:** no live step-by-step state transfer is currently performed.

---

# Project Validation

`validate_project.py` executes the `validate_all.py` script for each engine.

**Purpose:** validate the four engine implementations together using one project-wide command.

**Exit code:** returns `0` only if all engine validations pass; otherwise returns `1`.

**Failure handling:** a failure in one validation suite does not prevent the remaining suites from running.

---

# Directory Structure

```text
Integrated Systems Oncology/
│
├── master_engine.py
├── validate_project.py
├── README.md
├── CITATION.cff
├── VERSION.md
├── DATE.md
├── LICENSE.md
│
├── engines/
│   ├── tumor_evolution/
│   ├── metabolism/
│   ├── epigenetics/
│   └── synergy/
│
├── documentation/
│   ├── MODEL_EQUATIONS.md
│   ├── PARAMETERS.md
│   └── ARCHITECTURE.md
│
├── manuscript/
│   ├── main.tex
│   └── Integrated_Systems_Oncology.pdf
│
├── archive/
│   ├── main.tex
│   ├── Integrated_Systems_Oncology.pdf
│   └── 16 legacy figures
│
├── figures/
└── outputs/
```

---

# Data Flow

1. Each engine validates its configuration at construction.
2. Each engine initializes its own state.
3. Each engine runs its simulation loop and records `SimulationResults`.
4. Each engine performs internal state checks when `strict_validation` is enabled.
5. The master captures each subprocess's console output and runtime.
6. The project validator launches the engine validation suites and aggregates PASS/FAIL status.

The current framework does not use a shared mutable state layer and does not automatically feed one engine's full trajectory into another engine during a run.

---

# Extensibility

The architecture is designed to accommodate additional engines or richer coupling mechanisms.

**Adding a new engine:**
- Create a new directory under `engines/`.
- Provide an `engine.py` with a configuration object, result object, simulation class, and `run()` entry point.
- Add one or more validators and a `validate_all.py` aggregator.
- Update `master_engine.py` and `validate_project.py` when the new engine is intended to be part of the core framework.

**Potential future extensions:**
- Step-synchronized cross-engine state transfer.
- Higher-dimensional spatial models.
- Immune-cell dynamics.
- Therapeutic intervention and PK/PD modules.
- Patient-specific calibration.
- Formal uncertainty quantification and sensitivity analysis.
- Benchmarking against established models.
- Parallel parameter sweeps and visualization utilities.

---

# Design Principles

- **Single responsibility** – each engine represents a defined biological/computational layer.
- **Modularity** – engines are self-contained and independently testable.
- **Reproducibility** – stochastic processes use seeded NumPy generators.
- **Validation first** – every engine has a dedicated validation suite.
- **Scientific transparency** – equations, defaults, assumptions, and limitations are documented.
- **Separation of evidence tiers** – software validation is not presented as biological or clinical validation.
