# Integrated Systems Oncology

**Version 1.0.2**

Welcome.

Integrated Systems Oncology (ISO) is a modular computational oncology framework that models tumour evolution, metabolism, epigenetics, and their systems-level interactions. It is designed for reproducible, seed-controlled, mechanistic computational simulations.

The framework consists of four standalone engine modules, each addressing a distinct biological layer, and a master orchestrator that runs them sequentially. Every engine is validated independently, and a project-wide validation suite checks the four engines together.

> **Release note:** The manuscript included in `manuscript/` documents software version **1.0.1**. Version **1.0.2** is a repository and documentation synchronization release; the simulation-engine source code is unchanged.

---

## Features

- **Tumor Evolution Engine** – Clonal population dynamics, driver/passenger mutation generation, lineage tracking, and diversity metrics.
- **Metabolism Engine** – 1D reaction-diffusion dynamics for oxygen, glucose, lactate, ATP, pH, ROS, hypoxia, necrosis, and metabolic phenotypes.
- **Epigenetics Engine** – Dynamic DNA methylation, histone acetylation, chromatin accessibility, gene-expression potential, instability, plasticity, stemness, differentiation, and epigenetic age.
- **Synergy Engine** – Systems-level aggregation of evolutionary, metabolic, and epigenetic fitness with explicit feedback terms for stress, mutation pressure, resistance, adaptation, resilience, and stability.
- **Seed-reproducible simulations** – Repeated runs with the same configuration and random seed reproduce the recorded numerical histories on the same platform.
- **Built-in validation suites** – Validators check implemented relationships, numerical stability, state invariants, and reproducibility.
- **Project-wide validation** – One command runs all four engine validation suites.
- **Modular architecture** – Engines are independently reusable; the current master orchestrator runs them sequentially and does not perform live step-by-step state transfer between engines.

---

## Architecture

The framework is organised into four independent engines, each modelling a different layer of tumour biology:

| Engine | Purpose |
|--------|---------|
| **Tumor Evolution** | Clonal evolution, mutation generation, lineage formation, population growth, and diversity. Growth is driven by stochastic birth and death processes with density-dependent competition. |
| **Metabolism** | Spatiotemporal dynamics of oxygen, glucose, lactate, ATP, pH, ROS, hypoxia, necrosis, and metabolic phenotypes on a 1D spatial grid. |
| **Epigenetics** | Dynamic regulation of DNA methylation, histone acetylation, chromatin accessibility, gene-expression potential, instability, plasticity, stemness, differentiation, and epigenetic age. |
| **Synergy** | Systems-level interaction among modelled evolutionary, metabolic, and epigenetic state variables, using weighted fitness aggregation and bounded feedback dynamics. |

The engines can be executed independently or sequentially through the master orchestrator. They expose Python APIs such as `run()` and region-level getter methods for external use and future coupling.

---

## Folder Structure

```text
Integrated Systems Oncology/
│
├── master_engine.py                 # Sequentially orchestrates the four engines
├── validate_project.py              # Project-wide validation suite
├── README.md                        # This file
├── CITATION.cff                     # Software citation metadata
├── VERSION.md                       # Repository version
├── LICENSE.md                       # Apache 2.0 license
│
├── engines/
│   ├── tumor_evolution/
│   │   ├── engine.py
│   │   ├── validate_all.py
│   │   └── ... (individual validators)
│   │
│   ├── metabolism/
│   │   ├── engine.py
│   │   ├── validate_all.py
│   │   └── ... (individual validators)
│   │
│   ├── epigenetics/
│   │   ├── engine.py
│   │   ├── validate_all.py
│   │   └── ... (individual validators)
│   │
│   └── synergy/
│       ├── engine.py
│       ├── validate_all.py
│       └── ... (individual validators)
│
├── documentation/                  # Architecture, equations, parameters, plans, and logs
├── manuscript/                     # Active manuscript source and PDF (documents v1.0.1)
├── archive/                        # Superseded manuscript and 16 legacy figures
├── figures/                        # Example/output placeholder information
└── outputs/                        # Example/output placeholder information
```

---

## Design Principles

- Modular by construction
- Reproducible by default
- Biological assumptions are explicit
- Validation accompanies every engine
- Software validation is distinguished from biological validation
- Each engine can be used separately or orchestrated with the full framework

---

## Software Statistics

Simulation Engines: 4  
Validation Suites: 4  
Individual Validators: 18  
Master Orchestrator: 1  
Project Validator: 1  
Language: Python  
Dependencies: NumPy  
Architecture: Modular  
Repository Version: 1.0.2  
Documented Manuscript Version: 1.0.1

---

## Requirements

- **Python** ≥ 3.11
- **NumPy** ≥ 1.24

The code uses only the Python standard library plus NumPy. No other external dependencies are required.

---

## Installation

Clone the repository:

```bash
git clone https://github.com/Dewan-Sajid-Islam/Integrated-Systems-Oncology.git
cd Integrated-Systems-Oncology
```

Ensure Python 3.11+ and NumPy are installed:

```bash
python --version
pip install numpy
```

No additional build steps are required.

---

## Running Individual Engines

Each engine can be executed directly by running its `engine.py` script.

```bash
python engines/tumor_evolution/engine.py
python engines/metabolism/engine.py
python engines/epigenetics/engine.py
python engines/synergy/engine.py
```

You can also import an engine and customise its `SimulationConfig` to change parameters, time steps, seeds, and other settings.

---

## Running the Master Engine

The master orchestrator runs all four engines sequentially as separate subprocesses:

```bash
python master_engine.py
```

The output reports the execution status and runtime for each engine. The current master does not transfer complete live state trajectories between engines; each engine runs to completion independently.

---

## Running Validation

### Engine-specific validation

Each engine contains a `validate_all.py` script that executes its full validation suite:

```bash
python engines/tumor_evolution/validate_all.py
python engines/metabolism/validate_all.py
python engines/epigenetics/validate_all.py
python engines/synergy/validate_all.py
```

### Project-wide validation

To validate all engines together:

```bash
python validate_project.py
```

The project validator runs every `validate_all.py` in sequence, collects the results, and exits with code 0 only when all engine validations pass.

---

## Validation Philosophy

Validation in ISO targets the software implementation and the directionality/consistency of implemented relationships. It does **not** establish biological or clinical correctness. The suites check finite and bounded state variables, internal invariants, expected directional responses under test conditions, lineage/state validity where applicable, and reproducibility under identical seeds.

---

## Scientific Scope

The current release is intentionally limited to the four implemented engines. It does not currently include an explicit immune-cell model, therapeutic intervention or PK/PD model, patient-specific calibration, formal uncertainty quantification, three-dimensional spatial structure, or live step-by-step cross-engine state coupling. These are documented as future work rather than current capabilities.

---

## Citation

Software citation metadata is maintained in `CITATION.cff`.

Zenodo v1.0.2 DOI: 10.5281/zenodo.22980897

The manuscript in `manuscript/` documents v1.0.1 and therefore retains its v1.0.1 version-specific Zenodo DOI.

---

## License

Apache License 2.0. See `LICENSE.md`.

---

## Status

**Repository version:** 1.0.2  
**Manuscript version:** 1.0.1  
**Project status:** Stable, validated, reproducible  
**Type:** Research software

Version 1.0.2 is a documentation and release-metadata synchronization update. The four engine implementations and their validation logic are unchanged from the documented v1.0.1 software release.
