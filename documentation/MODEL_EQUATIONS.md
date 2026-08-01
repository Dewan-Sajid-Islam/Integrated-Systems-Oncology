# Integrated Systems Oncology
## Mathematical Model Specification

**Version 1.0.0**

This document provides the complete mathematical specification of the Integrated Systems Oncology (ISO) software framework. Every biological process, from clonal evolution to metabolic dynamics and epigenetic regulation, is represented by a set of deterministic and stochastic equations. All models are designed to be interpretable, reproducible, and grounded in established cancer biology. The equations below correspond exactly to the implementation in each engine's `SimulationConfig` and update logic.

---

# Tumor Evolution Engine

The Tumor Evolution Engine models clonal population dynamics, mutation accumulation, selection, and lineage formation.

## Logistic Growth

Population growth is density‑dependent, following a logistic equation:

$$
\frac{dP}{dt} = r P \left(1 - \frac{N}{K}\right)
$$

where:
- \(P\) is the population of a specific clone.
- \(N\) is the total tumour burden (sum of all clones).
- \(K\) is the carrying capacity (`carrying_capacity`).
- \(r\) is the net growth rate (`growth_rate` per clone).

## Birth–Death Dynamics

In the mechanistic version (v0.5+), growth is decomposed into birth and death rates:

$$
\text{net growth} = \text{effective birth} - \text{effective death}
$$

with:
- Effective birth rate:  
  \( b_i = b_0 \cdot \text{proliferation}_i \cdot \text{metabolic efficiency}_i \cdot (1 - N/K) \)
- Effective death rate:  
  \( d_i = d_0 \cdot \text{apoptosis susceptibility}_i \cdot (1 + \text{immune visibility}_i) \)

where \(b_0\) and \(d_0\) are base rates from configuration.

## Mutation Probability

Mutations occur during cell division. The expected number of mutations for a clone is:

$$
\lambda_i = \text{new\_cells}_i \cdot \mu_i
$$

where:
- \(\text{new\_cells}_i\) = number of births in the current time step.
- \(\mu_i\) = effective mutation rate = \(\mu_0 \cdot \frac{1}{\text{repair}} \cdot (1 + \text{instability})\).

## Driver and Passenger Mutations

Each mutation is classified as either driver (fraction `driver_mutation_probability`) or passenger. For drivers, the effect on growth rate is drawn from an exponential distribution (mean `driver_effect_mean`). Passengers have normally distributed effects (`passenger_effect_std`).

## Clone Fitness

Fitness is a derived quantity:

$$
\text{fitness}_i = \text{growth\_rate}_i \cdot \text{proliferation}_i \cdot \text{metabolic\_efficiency}_i \cdot \frac{1}{1 + \text{immune\_visibility}_i} \cdot (1 + 0.02 \cdot \text{plasticity})
$$

It is used for selection.

## Selection (Replicator Dynamics)

Selection is applied after growth and mutation:

$$
P_i \leftarrow P_i \cdot \frac{\text{fitness}_i}{\overline{\text{fitness}}}
$$

followed by renormalisation to maintain total burden. This mimics differential reproductive success.

## Lineage Formation

Each clone stores:
- `parent_id` (None for roots),
- `generation` (depth from root),
- `root_ancestor` (original clone of the lineage),
- `birth_time` (time step of creation).

## Diversity Metrics

Shannon diversity:

$$
H = - \sum_i p_i \ln p_i, \quad p_i = \frac{P_i}{N}
$$

Simpson diversity:

$$
D = 1 - \sum_i p_i^2
$$

---

# Metabolism Engine

The Metabolism Engine simulates spatiotemporal dynamics of key metabolites across a 1D grid of regions.

## Diffusion

For a substance \(S\), diffusion is modelled with a discrete Laplacian:

$$
\frac{\partial S_i}{\partial t} = D_S \cdot (S_{i-1} - 2S_i + S_{i+1})
$$

with zero‑flux boundaries except at vascular regions (fixed supply).

## Oxygen Consumption

Oxygen is consumed by cells (non‑necrotic) at a rate proportional to oxygen concentration and the fraction of metabolism that is oxidative:

$$
\text{O}_2^{\text{consumed}} = k_{\text{O}_2} \cdot O_2 \cdot (1 - \text{glycolytic\_fraction}) \cdot \Delta t
$$

## Glucose Consumption

Glucose consumption is proportional to glucose concentration and increases with glycolytic fraction:

$$
\text{Glu}^{\text{consumed}} = k_{\text{Glu}} \cdot \text{Glu} \cdot (1 + \text{glycolytic\_fraction}) \cdot \Delta t
$$

## Warburg Effect

The glycolytic fraction is:

$$
\text{glycolytic\_fraction} = \text{warburg\_bias} + (1 - \text{warburg\_bias}) \cdot (1 - \text{oxygen\_norm}) + \text{aerobic\_glycolysis\_fraction}
$$

clipped to [0,1]. This captures aerobic glycolysis (Warburg effect).

## ATP Production

ATP is produced from glycolysis and oxidative phosphorylation:

$$
\text{ATP}_{\text{glyc}} = \text{Glu}^{\text{consumed}} \cdot \text{glycolytic\_fraction} \cdot \text{glycolytic\_ATP\_yield}
$$

$$
\text{ATP}_{\text{OXPHOS}} = \text{Glu}^{\text{consumed}} \cdot (1 - \text{glycolytic\_fraction}) \cdot \text{oxidative\_ATP\_yield} \cdot \text{mito\_efficiency}
$$

Total ATP production:

$$
\text{ATP}^{\text{prod}} = \text{ATP}_{\text{glyc}} + \text{ATP}_{\text{OXPHOS}}
$$

## ROS Dynamics

ROS is produced from OXPHOS and decays naturally:

$$
\frac{d\text{ROS}}{dt} = k_{\text{ROS}}^{\text{prod}} \cdot \text{ATP}_{\text{OXPHOS}} - k_{\text{ROS}}^{\text{decay}} \cdot \text{ROS}
$$

## Lactate Production

Lactate is produced from glycolysis:

$$
\text{Lac}^{\text{prod}} = \text{Glu}^{\text{consumed}} \cdot \text{glycolytic\_fraction} \cdot k_{\text{Lac}}
$$

## pH Dynamics

pH decreases with lactate accumulation and has buffering:

$$
\frac{d\text{pH}}{dt} = -k_{\text{acid}} \cdot \text{Lac} + k_{\text{buff}} \cdot (\text{pH}_0 - \text{pH})
$$

## Necrosis

Necrosis occurs when:
- ATP falls below `necrosis_atp_threshold`.
- Stress exceeds `necrosis_stress_threshold`.
- These conditions persist for `necrosis_duration_threshold` steps.

Necrotic regions stop consuming nutrients and ATP production.

## Phenotype Assignment

Based on oxygen, ATP, and stress, each region is assigned to one of:
- OXIDATIVE
- GLYCOLYTIC
- INTERMEDIATE
- HYPOXIC
- QUIESCENT
- NECROTIC

using a set of threshold rules.

---

# Epigenetics Engine

The Epigenetics Engine models dynamic changes in chromatin state and cell identity.

## DNA Methylation

Methylation dynamics include passive drift, active demethylation, and stress effects:

$$
\frac{d\text{Met}}{dt} = k_{\text{drift}} \cdot (\text{Met}_{\text{eq}} - \text{Met}) + k_{\text{demeth}} \cdot \text{Ace} \cdot (1 - \text{Met}) + k_{\text{stress}} \cdot \text{stress} \cdot (0.5 - \text{Met})
$$

## Histone Acetylation

Acetylation dynamics:

$$
\frac{d\text{Ace}}{dt} = k_{\text{ac}} \cdot (1 - \text{Ace}) - k_{\text{deac}} \cdot \text{Ace} + k_{\text{stress\_ac}} \cdot \text{stress} \cdot (0.5 - \text{Ace})
$$

## Chromatin Accessibility

Accessibility is driven by acetylation (opening) and methylation (closing):

$$
\frac{d\text{Acc}}{dt} = k_{\text{open}} \cdot \text{Ace} \cdot (1 - \text{Acc}) - k_{\text{close}} \cdot \text{Met} \cdot \text{Acc}
$$

## Gene Expression Potential

Expression is a linear combination plus noise:

$$
\text{Expr} = \text{base} + \alpha \cdot \text{Ace} + \beta \cdot \text{Met} + \gamma \cdot \text{Acc} + \mathcal{N}(0, \sigma_{\text{noise}}^2)
$$

## Instability

Instability increases with stress and decays:

$$
\frac{d\text{Inst}}{dt} = k_{\text{inst,base}} + k_{\text{inst,stress}} \cdot \text{stress} - k_{\text{inst,decay}} \cdot \text{Inst}
$$

## Plasticity

Plasticity is driven by instability:

$$
\frac{d\text{Plas}}{dt} = k_{\text{plas,base}} + k_{\text{plas,inst}} \cdot \text{Inst} - k_{\text{plas,decay}} \cdot \text{Plas}
$$

## Stemness and Differentiation

Stemness decreases with differentiation and increases with plasticity/resilience:

$$
\frac{d\text{Stem}}{dt} = -k_{\text{diff,stem}} \cdot \text{Diff} \cdot \text{Stem} + k_{\text{stem,plas}} \cdot \text{Plas} \cdot (1 - \text{Stem}) - k_{\text{stress,stem}} \cdot \text{stress} \cdot \text{Stem}
$$

Differentiation increases towards completion and can be reversed by plasticity:

$$
\frac{d\text{Diff}}{dt} = k_{\text{diff}} \cdot (1 - \text{Diff}) \cdot (1 + 2(1 - \text{Stem})) - k_{\text{stem,plas}} \cdot \text{Plas} \cdot \text{Diff}
$$

## Epigenetic Age

Age accumulates over time and is partially reset by high plasticity:

$$
\frac{d\text{Age}}{dt} = k_{\text{age}} - k_{\text{reset}} \cdot \text{Plas} \cdot \text{Age}
$$

---

# Synergy Engine

The Synergy Engine integrates outputs from the three previous engines into a unified systems model.

## Combined Fitness

$$
\text{CombinedFitness} = w_{\text{tumor}} \cdot \text{TumorFitness} + w_{\text{met}} \cdot \text{MetabolicFitness} + w_{\text{epi}} \cdot \text{EpigeneticFitness}
$$

## Mutation Pressure

Mutation pressure is driven by metabolic and oxidative stress:

$$
\frac{d\text{Mut}}{dt} = k_{\text{mut,met}} \cdot \text{MetStress} \cdot (1 - \text{Mut}) + k_{\text{mut,ox}} \cdot \text{OxStress} \cdot (1 - \text{Mut}) - k_{\text{mut,decay}} \cdot \text{Mut}
$$

## Therapy Resistance

Resistance is driven by plasticity and resilience:

$$
\frac{d\text{Resist}}{dt} = k_{\text{res,plas}} \cdot \text{Plas} \cdot (1 - \text{Resist}) + k_{\text{res,resil}} \cdot \text{Resil} \cdot (1 - \text{Resist}) - k_{\text{res,decay}} \cdot \text{Resist}
$$

## Adaptive Capacity

Adaptive capacity increases with gene expression and saturates:

$$
\frac{d\text{Adapt}}{dt} = k_{\text{adapt,expr}} \cdot \text{GeneExpr} \cdot (\text{Sat} - \text{Adapt}) - k_{\text{adapt,decay}} \cdot \text{Adapt}
$$

## Cellular Resilience

Resilience is increased by stemness and decreased by stress:

$$
\frac{d\text{Resil}}{dt} = k_{\text{resil,stem}} \cdot \text{Stem} \cdot (1 - \text{Resil}) - k_{\text{stress,resil}} \cdot \text{MetStress} \cdot \text{Resil}
$$

## System Stability

Stability is increased by resilience and decreased by oxidative stress and mutation pressure:

$$
\frac{d\text{Stab}}{dt} = k_{\text{stab,resil}} \cdot \text{Resil} \cdot (1 - \text{Stab}) - k_{\text{stab,ox}} \cdot \text{OxStress} \cdot \text{Stab} - k_{\text{stab,mut}} \cdot \text{Mut} \cdot \text{Stab}
$$

## Stress Dynamics

- Hypoxia drives metabolic stress:  
  \(\text{MetStress} = \alpha \cdot \text{Hypoxia} + \beta \cdot \text{OxStress}\)
- Oxidative stress increases with metabolic fitness and decays.
- Metabolic stress decays towards baseline.

## Negative Feedback

High therapy resistance reduces selection pressure, and high mutation pressure reduces epigenetic fitness, providing homeostatic regulation.

---

# Numerical Integration

All engines use **explicit Euler integration**:

$$
x_{t+1} = x_t + f(x_t) \cdot \Delta t
$$

where \(\Delta t\) is the time step (`dt`). This method is simple, efficient, and sufficiently accurate for the time scales and dynamics considered.

**Numerical stability** is ensured by:
- Small \(\Delta t\) relative to the fastest rates.
- Clipping variables to their biological bounds (e.g., [0,1]).
- Using bounded growth terms (e.g., \( \text{rate} \cdot (1 - x) \)) to prevent overshoot.

---

# Assumptions

- **Resource limitation** – Carrying capacity limits population growth.
- **Spatial homogeneity within regions** – Each engine treats a region as well‑mixed.
- **Simplified mutation effects** – Only growth rate and phenotype traits are mutated; no explicit gene‑level modelling.
- **Deterministic integration** – Stochastic events (mutations, births, deaths) are drawn from Poisson/normal distributions but are seeded for reproducibility.
- **Decoupled time scales** – Each engine runs with its own time step; coupling is only through final outputs (not simultaneous integration).
- **No therapy, immune, or clinical data** – These are reserved for future engines.

These assumptions make the framework interpretable and computationally tractable while still capturing the key biological processes of cancer evolution, metabolism, and epigenetics.