# Integrated Systems Oncology
## Mathematical Model Specification

**Repository Version 1.0.2**

This document records the mathematical update rules implemented by the current ISO source code. The Tumor Evolution Engine is a discrete stochastic process; the Metabolism, Epigenetics, and Synergy Engines update continuous state variables by explicit time-stepping. Parameters named below correspond to fields in the engines' `SimulationConfig` objects. The equations are written in compact mathematical notation; clipping, non-negativity enforcement, thresholds, and categorical state rules are part of the implementation.

> **Important:** these equations describe the implemented computational model. They are not claims of biological validation, clinical efficacy, or empirical parameter calibration.

---

# Tumor Evolution Engine

Let `P_i` be the population of clone `i`, and let `N = Σ_i P_i` over alive clones. Let `K` be `carrying_capacity`.

## Birth rate and stochastic births

The effective birth rate is

$$
b_i = b_0 \, \phi_i \, \eta_i \, \max\left(0,1-\frac{N}{K}\right),
$$

where `b_0 = default_growth_rate + death_rate`, `φ_i` is `proliferation_capacity`, and `η_i` is `metabolic_efficiency`.

The realized number of births is drawn from

$$
B_i \sim \mathrm{Poisson}(b_i P_i).
$$

The current implementation uses one simulation time unit per discrete growth/mutation step rather than an explicit `dt` parameter in this engine.

## Death rate and stochastic deaths

The effective death rate is

$$
d_i = d_0 \, \alpha_i \, (1+\nu_i),
$$

where `d_0 = death_rate`, `α_i` is `apoptosis_susceptibility`, and `ν_i` is `immune_visibility`.

Deaths are sampled as

$$
D_i \sim \mathrm{Poisson}(d_i P_i).
$$

Population update:

$$
P_i \leftarrow \max(0,P_i+B_i-D_i).
$$

There is no explicit replicator-dynamics rescaling step. Differential net expansion produces emergent selection.

## Mutation process

The effective mutation rate per division is

$$
\mu_i = \mu_0 \, \frac{1}{\max(0.1,\rho_i)}(1+\iota_i),
$$

where `μ0 = mutation_rate`, `ρ_i` is `dna_repair_efficiency`, and `ι_i` is `genomic_instability`.

Mutation attempts are sampled as

$$
M_i \sim \mathrm{Poisson}(B_i\mu_i m_d),
$$

where `m_d = development_mutation_multiplier` when `development_mode` is enabled, otherwise `m_d = 1`.

Each attempt is classified as driver with probability `driver_mutation_probability`; otherwise it is a passenger. Each attempt then establishes a new lineage with probability `lineage_establishment_probability`, except that development mode uses an elevated establishment probability of 0.3 for testing visibility.

Successful establishments:
- take a seed population equal to `max(1.0, 0.005 * parent_population)` from the parent;
- inherit the parent's phenotype traits;
- mutate one or more phenotype traits;
- record a structured `Mutation` event and lineage metadata.

Mutation effects are sampled from zero-centered normal distributions. Driver mutations use `driver_effect_scale`; passenger mutations use `passenger_effect_scale`.

## Fitness and diversity

Fitness is an observable derived from the effective rates:

$$
f_i = b_i-d_i.
$$

Shannon diversity:

$$
H = -\sum_i p_i\ln p_i, \qquad p_i=\frac{P_i}{N}.
$$

Simpson diversity:

$$
D = 1-\sum_i p_i^2.
$$

---

# Metabolism Engine

The Metabolism Engine uses a 1D grid of regions. State variables are oxygen `O`, glucose `G`, lactate `L`, ATP, pH, and ROS. The continuous variables are updated by explicit time-stepping.

## Diffusion

For a field `C`, the implementation uses a discrete Laplacian-like flux

$$
\mathcal{D}_j = D_C(C_{j-1}-2C_j+C_{j+1})
$$

for internal regions, with endpoint treatment corresponding to zero-flux-style boundary updates. Vascular regions are subsequently reset to their configured oxygen/glucose supply values.

## Warburg / glycolytic fraction

For non-necrotic regions, normalized oxygen is

$$
\tilde O_j = \mathrm{clip}(O_j,0,1).
$$

The glycolytic fraction is

$$
g_j = \mathrm{clip}\left(w + (1-w)(1-\tilde O_j)+a,0,1\right),
$$

where `w = warburg_bias` and `a = aerobic_glycolysis_fraction`.

## Consumption

Oxygen consumption:

$$
O^{\mathrm{cons}}_j = k_{O_2}O_j(1-g_j)\Delta t.
$$

Glucose consumption:

$$
G^{\mathrm{cons}}_j = k_GG_j(1+g_j)\Delta t.
$$

Necrotic regions have zero consumption and production.

## ATP production

Glycolytic ATP:

$$
ATP^{\mathrm{glyc}}_j = G^{\mathrm{cons}}_j g_j y_g.
$$

OXPHOS ATP:

$$
ATP^{\mathrm{OXPHOS}}_j = G^{\mathrm{cons}}_j(1-g_j)y_o\epsilon,
$$

where `y_g = glycolytic_atp_yield`, `y_o = oxidative_atp_yield`, and `ε = mitochondrial_efficiency_base`.

Total ATP production is the sum of the two terms.

ATP also has a basal consumption term of `0.1 * ATP * dt` in the implementation.

## Lactate and ROS

Lactate production:

$$
L^{\mathrm{prod}}_j = G^{\mathrm{cons}}_j g_j k_L.
$$

ROS production is proportional to OXPHOS ATP:

$$
ROS^{\mathrm{prod}}_j = k_{ROS}ATP^{\mathrm{OXPHOS}}_j.
$$

ROS then decays at first order with `ros_decay_rate` and receives a fixed diffusion contribution using diffusion coefficient `0.02`.

## pH

pH changes according to

$$
\Delta pH_j = -k_{acid}L_j\Delta t + k_{buff}(pH_0-pH_j)\Delta t + \mathcal{D}^{pH}_j\Delta t.
$$

The pH state is clipped to `[0,14]`.

## Stress, hypoxia, and phenotype classification

Hypoxia is true for non-necrotic regions with

$$
O_j < oxygen\_threshold_{hypoxia}.
$$

Stress is calculated from ATP deficit, lactate stress, and pH stress:

$$
Stress_j = 0.4A_j + 0.3L_j + 0.3P_j,
$$

where

$$
A_j=\max\left(0,1-\frac{ATP_j}{ATP_{initial}}\right),
$$

$$
L_j=\mathrm{clip}\left(\frac{L_j}{0.5},0,1\right),
$$

and

$$
P_j=\mathrm{clip}\left(\frac{7.4-pH_j}{1.0},0,1\right).
$$

Necrosis is triggered when stress exceeds `necrosis_stress_threshold` and ATP is below `necrosis_atp_threshold` for the required number of consecutive steps. Once necrotic, a region remains necrotic and its metabolic state is reset to inactive values.

Phenotypes are assigned from oxygen, ATP, and stress thresholds as `OXIDATIVE`, `GLYCOLYTIC`, `INTERMEDIATE`, `HYPOXIC`, `QUIESCENT`, or `NECROTIC`.

---

# Epigenetics Engine

For region `j`, let `Met`, `Ace`, `Acc`, `Exp`, `Inst`, `Plas`, `Stem`, `Diff`, `Stress`, and `Age` denote the corresponding state variables. All are updated by explicit time-stepping and normalized state variables are clipped to `[0,1]` where applicable.

## Stress

The stress update is

$$
Stress_{t+1}=\mathrm{clip}\left(Stress_t + s_{base}\Delta t + s_{inst}Inst_t\Delta t - s_{decay}Stress_t\Delta t,0,1\right).
$$

## DNA methylation

$$
\frac{dMet}{dt} = k_{drift}(M_{eq}-Met) + k_{demeth}Ace(1-Met) + k_{stress}Stress(0.5-Met).
$$

## Histone acetylation

$$
\frac{dAce}{dt} = k_{ac}(1-Ace)-k_{deac}Ace+k_{stress,ac}Stress(0.5-Ace).
$$

## Chromatin accessibility

$$
\frac{dAcc}{dt}=k_{open}Ace(1-Acc)-k_{close}Met\,Acc.
$$

## Gene-expression potential

$$
Exp = e_0 + \alpha_AAce + \alpha_MMet + \alpha_XAcc + \xi,
$$

where

$$
\xi\sim\mathcal{N}(0,\sigma_E^2).
$$

The implementation clips expression at zero after adding stochastic noise.

## Instability and plasticity

$$
\frac{dInst}{dt}=k_{inst,base}+k_{inst,stress}Stress-k_{inst,decay}Inst,
$$

$$
\frac{dPlas}{dt}=k_{plas,base}+k_{plas,inst}Inst-k_{plas,decay}Plas.
$$

## Stemness and differentiation

$$
\frac{dStem}{dt}=-k_{diff,stem}Diff\,Stem+k_{stem,plas}Plas(1-Stem)+k_{stem,stress}Stress\,Stem,
$$

where `stemness_stress_factor` is negative in the default configuration.

Differentiation evolves as

$$
\frac{dDiff}{dt}=k_{diff}(1-Diff)(1+2(1-Stem))-k_{stem,plas}Plas\,Diff.
$$

The continuous differentiation and chromatin states are converted to discrete categories using thresholds on differentiation and accessibility.

## Epigenetic age

$$
\frac{dAge}{dt}=k_{age}-k_{reset}Plas\,Age.
$$

---

# Synergy Engine

Let `TF`, `MF`, and `EF` be tumor, metabolic, and epigenetic fitness; `CF` be combined fitness; and `MP`, `Sel`, `MS`, `Ox`, `Hyp`, `Plas`, `R`, `AC`, `Stem`, `Res`, and `Stab` denote mutation pressure, selection pressure, metabolic stress, oxidative stress, hypoxia, plasticity, resistance, adaptive capacity, stemness, resilience, and stability.

## Combined fitness

$$
CF=w_TTF+w_MMF+w_EEF,
$$
with weights constrained by configuration validation to sum to one.

## Hypoxia and oxidative stress

$$
\frac{dHyp}{dt}=k_H MS(1-Hyp)-\kappa_HHyp,
$$

$$
\frac{dOx}{dt}=k_O MF(1-Ox)-\kappa_OOx.
$$

Metabolic stress target:

$$
MS^*=w_HHyp+w_OOx,
$$

followed by bounded response and decay according to `metabolic_stress_response_rate` and `metabolic_stress_decay_rate`.

## Mutation pressure

$$
\frac{dMP}{dt}=k_{MP}\left(w_{MS}MS+w_{Ox}Ox\right)(1-MP)-\kappa_{MP}MP.
$$

## Selection pressure

The internal selection drive is

$$
S^*=(0.2CF+0.1Hyp)(1-0.3R),
$$

and selection pressure follows a bounded response/decay update using `selection_response_rate` and `selection_decay_rate`.

## Plasticity

The implemented plasticity drive is

$$
\frac{dPlas}{dt}=w_{MP\rightarrow Plas}^2 MP(1-Plas)-\kappa_{Plas}Plas,
$$

where the squared weight reflects the current source-code implementation.

## Therapy resistance

$$
\frac{dR}{dt}=k_R\left(w_{Plas}Plas+w_{Res}Res\right)(1-R)-\kappa_RR.
$$

## Chromatin accessibility and gene expression

Chromatin target:

$$
Acc^*=0.5+0.4Plas.
$$

Gene-expression drive uses the squared configured chromatin-expression weight:

$$
\frac{dExp}{dt}=w_{X}^2Acc(1-Exp)-0.02Exp.
$$

## Adaptive capacity

$$
\frac{dAC}{dt}=w_A^2Exp(1-AC)-0.02AC.
$$

## Stemness, resilience, and stability

Stemness:

$$
\frac{dStem}{dt}=w_{Stem}Res(1-Stem)-0.03Plas\,Stem-k_{stress,Stem}MS\,Stem.
$$

Resilience:

$$
\frac{dRes}{dt}=w_{Res}Stem(1-Res)-k_{stress,Res}MS\,Res-0.01Ox\,Res.
$$

Stability:

$$
\frac{dStab}{dt}=w_{Stab}Res(1-Stab)-0.06Ox\,Stab-0.04MP\,Stab.
$$

## Fitness component updates

The three component fitness variables are bounded to `[0,1]` using source-code update rules:

$$
\frac{dTF}{dt}=0.02(1-TF)(1-0.5MS)-0.02c_RRTF,
$$

$$
\frac{dMF}{dt}=0.02(1-MF)(1-0.5Ox)-0.02MP\,MF,
$$

$$
\frac{dEF}{dt}=0.02(1-EF)(1-0.5MP)-0.02c_MMP\,EF,
$$

where `c_R = resistance_fitness_cost` and `c_M = mutation_fitness_cost`.

---

# Numerical Treatment

Metabolism, Epigenetics, and Synergy use explicit time-stepping. In development mode, the effective `dt` is multiplied by the corresponding `development_dt_multiplier`.

Tumor Evolution uses discrete stochastic events with Poisson sampling and does not use Euler integration.

State bounds are enforced by clipping or threshold logic in the individual engines. Reproducibility is obtained from `numpy.random.default_rng(random_seed)`.

---

# Core Assumptions

- The spatial representation is one-dimensional in Metabolism and Epigenetics.
- Regions are treated as well-mixed compartments within the modeled grid.
- Tumor mutation effects are represented through phenotype traits rather than explicit gene-level molecular networks.
- The Synergy Engine is a model-level aggregation layer, not an empirical demonstration of therapeutic synergy.
- Parameters are implementation defaults and are not empirically calibrated in the current release.
- The current master orchestration does not perform live trajectory exchange among engines.
- Immune-cell dynamics, treatment administration, three-dimensional geometry, formal uncertainty quantification, and experimental/clinical validation are outside the current release scope.
