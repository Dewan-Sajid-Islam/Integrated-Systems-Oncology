# Integrated Systems Oncology
## Software Architecture

**Version 1.0.0**

This document describes the software architecture of the Integrated Systems Oncology (ISO) framework. It covers the high‑level design, module responsibilities, data flow, and principles that guide the implementation. The architecture is modular, reproducible, and built for scientific transparency.

---

# High-Level Architecture

The ISO framework is composed of four independent simulation engines, each modelling a distinct biological layer. They are orchestrated by a master script and validated by a project‑wide validation suite.

```
┌─────────────────────────────────────────────────────────────┐
│                     Master Engine                           │
│                 (master_engine.py)                          │
└─────────────────────────────────────────────────────────────┘
                           │
                           ▼
        ┌──────────────────────────────────────┐
        │      Tumor Evolution Engine          │
        │   (clonal evolution, mutations)      │
        └──────────────────────────────────────┘
                           │
                           ▼
        ┌──────────────────────────────────────┐
        │        Metabolism Engine             │
        │   (oxygen, glucose, ATP, pH, ROS)    │
        └──────────────────────────────────────┘
                           │
                           ▼
        ┌──────────────────────────────────────┐
        │       Epigenetics Engine             │
        │   (methylation, acetylation, stem)   │
        └──────────────────────────────────────┘
                           │
                           ▼
        ┌──────────────────────────────────────┐
        │         Synergy Engine               │
        │   (integration, fitness, resistance) │
        └──────────────────────────────────────┘
```

Each engine is self‑contained, with its own configuration, simulation loop, and validation suite. The master engine does not import or modify engine code; it runs each as a subprocess, collecting output and timing information.

---

# Module Responsibilities

## Tumor Evolution Engine

**Inputs:** `SimulationConfig` (random seed, carrying capacity, mutation rates, etc.)

**Outputs:** `SimulationResults` (tumour burden, clone populations, diversity, mutation records, lineage tree)

**Responsibilities:**
- Clonal population dynamics (birth, death, logistic growth).
- Mutation generation (driver/passenger, phenotype effects).
- Selection and fitness computation.
- Lineage tracking and validation.
- Deterministic RNG.

**Public API:**
- `run()` → `SimulationResults`
- `initialize_population()`, `shannon()`, `simpson()`, `get_clone_frequencies()`, `get_lineage_summary()`

---

## Metabolism Engine

**Inputs:** `SimulationConfig` (diffusion, consumption rates, vascular map, etc.)

**Outputs:** `SimulationResults` (oxygen, glucose, ATP, lactate, pH, ROS, hypoxia, necrosis, phenotype histories)

**Responsibilities:**
- 1D diffusion‑reaction for metabolites.
- Oxygen/glucose consumption, ATP production, ROS dynamics.
- Warburg effect, mitochondrial efficiency.
- Necrosis and phenotype assignment.
- Vascular supply.

**Public API:**
- `run()` → `SimulationResults`
- `get_region_*()` methods for each variable.
- `get_hypoxia_index()`, `get_necrosis_fraction()`, `get_metabolic_fitness()`.

---

## Epigenetics Engine

**Inputs:** `SimulationConfig` (methylation, acetylation, plasticity rates, etc.)

**Outputs:** `SimulationResults` (methylation, acetylation, accessibility, expression, instability, plasticity, stemness, differentiation, stress, age)

**Responsibilities:**
- Dynamic epigenetic state evolution.
- Coupled ordinary differential equations for chromatin state.
- Noise injection for gene expression.
- Discrete phenotype and chromatin state classification.

**Public API:**
- `run()` → `SimulationResults`
- `get_region_*()` methods.
- `get_average_epigenetic_fitness()`.

---

## Synergy Engine

**Inputs:** `SimulationConfig` (weights, feedback rates, initial values)

**Outputs:** `SimulationResults` (combined fitness, mutation pressure, therapy resistance, adaptive capacity, resilience, stability, stresses)

**Responsibilities:**
- Integration of tumour, metabolic, and epigenetic fitness.
- Modelling feedback loops (e.g., stress → mutation → plasticity → resistance).
- System‑level dynamics and stability.
- Maintaining deterministic reproducibility.

**Public API:**
- `run()` → `SimulationResults`
- `get_combined_fitness()`, `get_region_combined_fitness()`, `get_average_combined_fitness()`.

---

# Master Engine

`master_engine.py` orchestrates the execution of all four engines.

**Purpose:** Provide a single command to run the full ISO pipeline sequentially.

**Execution order:**
1. Tumor Evolution
2. Metabolism
3. Epigenetics
4. Synergy

**Failure handling:** If one engine fails (non‑zero exit code), the master engine continues with the remaining engines. It never crashes.

**Timing:** Each subprocess is timed and displayed in the final summary.

**Subprocess execution:** Each engine is run as `python engine.py` inside its own directory, with separate `stdout`/`stderr` capture.

---

# Project Validation

`validate_project.py` executes the `validate_all.py` script for each engine.

**Purpose:** Validate the entire project by running all engine‑specific validation suites.

**Engine validation:** Each engine's `validate_all.py` runs its own validators (e.g., growth, mutation, diversity, reproducibility).

**Exit codes:** Returns `0` only if all validations pass; otherwise `1`.

**Output:** Provides a summary table with PASS/FAIL and runtime per engine.

---

# Directory Structure

```
Integrated Systems Oncology/
│
├── master_engine.py                 # Orchestrator
├── validate_project.py              # Project‑wide validation
├── README.md
│
├── engines/
│   ├── tumor_evolution/
│   │   ├── engine.py
│   │   ├── validate_all.py
│   │   └── ... (validators)
│   ├── metabolism/
│   │   ├── engine.py
│   │   ├── validate_all.py
│   │   └── ... (validators)
│   ├── epigenetics/
│   │   ├── engine.py
│   │   ├── validate_all.py
│   │   └── ... (validators)
│   └── synergy/
│       ├── engine.py
│       ├── validate_all.py
│       └── ... (validators)
│
├── documentation/
│   ├── MODEL_EQUATIONS.md
│   ├── PARAMETERS.md
│   └── ARCHITECTURE.md
│
├── manuscript/                       # (future) manuscript files
├── outputs/                          # (future) simulation outputs
└── references/                       # (future) reference materials
```

---

# Data Flow

1. **Configuration** – Each engine reads its `SimulationConfig` (default or user‑provided).
2. **Simulation** – The engine initialises state and runs the simulation loop.
3. **Results** – All histories and summary statistics are stored in `SimulationResults`.
4. **Validation** – Validators run post‑simulation to check correctness.
5. **Output** – Console print summary; future versions may export to files.

All data flow is in‑memory; no file I/O is currently performed by the engines (except for potential future extensions).

---

# Extensibility

The ISO architecture is designed to be easily extended with new engines or modules.

**Adding a new engine:**
- Create a new directory under `engines/`.
- Include `engine.py` with a `SimulationConfig`, `SimulationResults`, and a main class that implements `run()`.
- Provide a `validate_all.py` validation suite.
- Update `master_engine.py` and `validate_project.py` to include the new engine.

**Why each engine is isolated:** Isolation ensures that:
- Bugs in one engine do not affect others.
- Engines can be developed and tested independently.
- Future engines can be added without modifying existing code.
- The framework remains modular and maintainable.

---

# Design Principles

- **Single Responsibility** – Each engine handles one biological domain.
- **Modularity** – Engines are self‑contained and communicate only through their public APIs.
- **Reproducibility** – All random processes are seeded; validations ensure deterministic behaviour.
- **Validation First** – Every engine has a comprehensive validation suite to verify correctness.
- **Deterministic Behaviour** – Given the same seed, results are identical across runs.
- **Scientific Transparency** – All parameters and equations are documented; code is clean and readable.

---

# Future Directions

Possible future enhancements (not implemented in Version 1.0.0):

- **Therapy Engine** – Model drug effects, resistance evolution, and dosing schedules.
- **Immune Engine** – Simulate immune cell infiltration and cytotoxicity.
- **Drug Response Engine** – Integrate pharmacodynamics and pharmacokinetics.
- **Clinical Data Interface** – Import patient data (e.g., imaging, genomics) to initialise simulations.
- **GPU Acceleration** – Speed up large‑scale simulations.
- **Visualisation** – Built‑in plotting and animation of simulation outputs.
- **Spatial 3D** – Extend 1D models to 2D or 3D.
- **Parallelisation** – Run multiple parameter sets concurrently.

The current architecture is designed to accommodate these extensions with minimal changes to existing modules.
```