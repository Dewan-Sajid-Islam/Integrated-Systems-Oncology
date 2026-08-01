# Integrated Systems Oncology

**Version 1.0.0**

Welcome.

Integrated Systems Oncology (ISO) is a modular computational oncology framework that models tumour evolution, metabolism, epigenetics, and their systems-level interactions. It is designed for reproducible, deterministic, and biologically mechanistic simulations of cancer progression.

The framework consists of four standalone engines, each addressing a distinct biological layer, and a master orchestrator that runs them in sequence. Every engine is validated independently, and a project‑wide validation suite ensures scientific reproducibility across the entire system.

---

## Features

- **Tumor Evolution Engine** – Clonal evolution, driver/passenger mutations, lineage tracking, and population dynamics.
- **Metabolism Engine** – Oxygen, glucose, lactate, ATP, ROS, hypoxia, Warburg effect, and metabolic phenotypes.
- **Epigenetics Engine** – DNA methylation, histone acetylation, chromatin accessibility, stemness, plasticity, and differentiation.
- **Synergy Engine** – Integration of tumour, metabolic and epigenetic fitness into a unified adaptive system.
- **Deterministic simulations** – Every run is reproducible using a random seed.
- **Built‑in validation suites** – Each engine includes multiple standalone validators that check mathematical, biological, and numerical correctness.
- **Project‑wide validation** – One command validates all four engines together.
- **Modular architecture** – Engines are independent and can be used separately or coupled.
- **Research‑ready** – Designed for publication‑quality computational systems biology.

---

## Architecture

The framework is organised into four independent engines, each modelling a different layer of tumour biology:

| Engine | Purpose |
|--------|---------|
| **Tumor Evolution** | Clonal evolution, mutation accumulation, lineage formation, population growth, and selection. Implements logistic growth, birth–death processes, and driver/passenger mutations with heritable phenotype traits. |
| **Metabolism** | Spatiotemporal dynamics of oxygen, glucose, lactate, ATP, pH, reactive oxygen species (ROS), and metabolic phenotypes. Includes diffusion, vascular supply, Warburg effect, mitochondrial efficiency, and necrosis. |
| **Epigenetics** | Dynamic regulation of DNA methylation, histone acetylation, chromatin accessibility, gene‑expression potential, instability, plasticity, stemness, differentiation, and epigenetic age. All variables evolve through coupled differential equations. |
| **Synergy** | Systems‑level integration of tumour fitness, metabolic fitness, and epigenetic fitness. Computes combined fitness, mutation pressure, therapy resistance, adaptive capacity, resilience, and system stability through biologically motivated feedback loops. |

The engines can be run independently or sequentially via the master orchestrator. Each engine exposes a public API (e.g., `run()`, `get_region_*()` methods) to facilitate future coupling and external integration.

---

## Folder Structure

```
Integrated Systems Oncology/
│
├── master_engine.py                 # Orchestrates all four engines
├── validate_project.py              # Project‑wide validation suite
├── README.md                        # This file
│
├── engines/
│   ├── tumor_evolution/
│   │   ├── engine.py
│   │   ├── validate_all.py
│   │   ├── validate_growth.py
│   │   ├── validate_mutation.py
│   │   ├── validate_diversity.py
│   │   ├── validate_lineage.py
│   │   └── validate_reproducibility.py
│   │
│   ├── metabolism/
│   │   ├── engine.py
│   │   ├── validate_all.py
│   │   ├── validate_diffusion.py
│   │   ├── validate_metabolism.py
│   │   ├── validate_phenotypes.py
│   │   └── validate_reproducibility.py
│   │
│   ├── epigenetics/
│   │   ├── engine.py
│   │   ├── validate_all.py
│   │   ├── validate_epigenetics.py
│   │   ├── validate_chromatin.py
│   │   ├── validate_differentiation.py
│   │   └── validate_reproducibility.py
│   │
│   └── synergy/
│       ├── engine.py
│       ├── validate_all.py
│       ├── validate_synergy.py
│       ├── validate_feedback.py
│       ├── validate_stability.py
│       ├── validate_adaptation.py
│       └── validate_reproducibility.py
│
├── documentation/                    # Project documentation
├── manuscript/                       # Manuscript files
├── outputs/                          # Simulation outputs
└── references/                       # Bibliography
```

## Design Principles

• Modular by construction

• Reproducible by default

• Deterministic whenever possible

• Validation accompanies every engine

• Biological assumptions are explicit

• Every simulation can be independently verified

• Each engine can be used separately or integrated with the full framework

---

## Software Statistics

Software Statistics

Simulation Engines: 4

Validation Suites: 4

Individual Validators: 18

Master Orchestrator: 1

Project Validator: 1

Language: Python

Dependencies: NumPy

Architecture: Modular

Version: 1.0.0

---

## Requirements

- **Python** ≥ 3.11
- **NumPy** ≥ 1.24

The code uses only the Python standard library plus NumPy. No other external dependencies are required.

---

## Installation

Clone the repository:

```bash
Clone the repository after it has been published.
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

Each engine can be executed directly by running its `engine.py` script. This will print a detailed simulation summary to the console.

```bash
python engines/tumor_evolution/engine.py
python engines/metabolism/engine.py
python engines/epigenetics/engine.py
python engines/synergy/engine.py
```

You can also import an engine and customise its `SimulationConfig` to change parameters, time steps, seed, etc.

---

## Running the Master Engine

The master orchestrator runs all four engines sequentially, capturing standard output and execution time.

```bash
python master_engine.py
```

The output will show a banner and a summary table with the status (PASS/FAIL) and runtime for each engine.

---

## Running Validation

### Engine‑specific validation

Each engine contains a `validate_all.py` script that executes its full validation suite. To validate a single engine:

```bash
python engines/tumor_evolution/validate_all.py
python engines/metabolism/validate_all.py
python engines/epigenetics/validate_all.py
python engines/synergy/validate_all.py
```

### Project‑wide validation

To validate all engines together:

```bash
python validate_project.py
```

This runs every `validate_all.py` in sequence, collects results, and prints a comprehensive project‑wide summary. The script exits with code 0 only if all validations pass.

---

## Validation Philosophy

- **Reproducibility** – All simulations are deterministic given the same random seed. The validation suite includes reproducibility tests that verify identical results for identical seeds.
- **Numerical stability** – Every variable is checked for finite values, no NaN/Inf, and correct bounds. Long simulations (500+ steps) are tested for stability.
- **Biological consistency** – The validators verify that the implemented relationships (e.g., mutation pressure increases with stress, resistance reduces fitness) behave correctly, and that state variables remain within biologically plausible ranges.
- **Modular testing** – Each engine has a dedicated set of validators that inspect its specific dynamics. These are combined in the project‑wide suite to ensure system‑level integrity.

---

## Scientific Philosophy

This software is built on the principle that **biology drives mathematics, mathematics drives simulation, and simulation produces reproducible computational evidence**.

Every equation and parameter in the framework has a biological interpretation. The code is not a black box; it is a transparent, modular, and extensible tool for investigating cancer systems biology. The accompanying manuscript documents the mathematical framework, biological assumptions, and validation results, ensuring that the software and publication are tightly coupled.

The framework is designed to be used by researchers, educators, and students as a basis for further development, hypothesis testing, and integration with other computational oncology tools.

---

## Citation

Read CITATION.cff

---

## License

Read LICENSE.md

---

## Status

**Version:** 1.0.0  
**Project status:** Stable, validated, reproducible  
**Type:** Research software  

All four engines are feature‑complete, fully validated, and ready for use in computational oncology studies. The framework is intended as a research software package for computational oncology and is designed to support reproducible scientific studies.