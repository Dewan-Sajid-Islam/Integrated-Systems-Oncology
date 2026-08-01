# validate_metabolism.py
"""
Validation of metabolism calculations.

Tests:
- Oxygen consumption occurs.
- Glucose consumption occurs.
- ATP production is positive.
- Lactate production occurs.
- ROS production occurs.
- pH decreases when lactate accumulates.
- Metabolic stress behaves consistently.
- ATP never becomes negative.
- All values remain finite.
"""

import sys
import numpy as np
from engine import SimulationConfig, MetabolismEngine


def test_metabolism():
    # Use a configuration with no diffusion (diffusion coefficients zero) to isolate metabolism.
    cfg = SimulationConfig(
        random_seed=42,
        time_steps=10,
        dt=0.1,
        num_regions=5,
        vascular_density=0.0,           # no supply (we'll set initial conditions)
        vascular_supply_oxygen=0.0,
        vascular_supply_glucose=0.0,
        diffusion_oxygen=0.0,
        diffusion_glucose=0.0,
        diffusion_lactate=0.0,
        diffusion_ph=0.0,
        oxygen_consumption_rate=0.05,
        glucose_consumption_rate=0.1,
        glycolytic_atp_yield=2.0,
        oxidative_atp_yield=36.0,
        lactate_production_rate=0.1,
        warburg_bias=0.5,
        aerobic_glycolysis_fraction=0.0,
        mitochondrial_efficiency_base=1.0,
        initial_ph=7.4,
        ph_acidification_rate=0.05,
        ph_buffering=0.1,
        ros_production_rate=0.02,
        ros_decay_rate=0.1,
        development_mode=False,
        strict_validation=False,
        initial_oxygen=1.0,
        initial_glucose=1.0,
        initial_lactate=0.0,
        initial_atp=0.5,
    )
    eng = MetabolismEngine(cfg)
    eng.initialize_state()
    # Record initial values.
    initial_O2 = eng.oxygen.copy()
    initial_Glu = eng.glucose.copy()
    initial_Lac = eng.lactate.copy()
    initial_ATP = eng.atp.copy()
    initial_ph = eng.ph.copy()
    initial_ROS = eng.ros.copy()

    # Run for several steps.
    for _ in range(5):
        eng._step()
        # Check non-negativity and finiteness.
        for arr in [eng.oxygen, eng.glucose, eng.lactate, eng.atp, eng.ph, eng.ros]:
            if not np.all(np.isfinite(arr)):
                print("  Non-finite value detected")
                return False
            if np.any(arr < -1e-9):
                print("  Negative value detected")
                return False

    # Check consumption: oxygen and glucose should have decreased.
    o2_decreased = np.mean(eng.oxygen) < np.mean(initial_O2)
    glu_decreased = np.mean(eng.glucose) < np.mean(initial_Glu)

    # Check ATP production: mean ATP increased.
    atp_increased = np.mean(eng.atp) > np.mean(initial_ATP)

    # Check lactate production: lactate increased.
    lac_increased = np.mean(eng.lactate) > np.mean(initial_Lac)

    # Check ROS production: ROS increased.
    ros_increased = np.mean(eng.ros) > np.mean(initial_ROS)

    # Check pH decrease: pH decreased (if lactate increased).
    ph_decreased = np.mean(eng.ph) < np.mean(initial_ph)

    # Check stress: should increase (as ATP deficit and lactate increase).
    # We need to compute stress; we can compute a simple metric: stress = 0.4*(1-ATP/initial) + ...
    # We'll compare mean stress from engine's stress attribute.
    initial_stress = np.mean(eng.stress)  # after initialization, stress is zero.
    # After steps, stress should be > 0.
    stress_increased = np.mean(eng.stress) > 0.0

    # ATP never negative (already checked).

    passed = (o2_decreased and glu_decreased and atp_increased and lac_increased and
              ros_increased and ph_decreased and stress_increased)

    print("validate_metabolism")
    print(f"  Oxygen consumption: {o2_decreased}")
    print(f"  Glucose consumption: {glu_decreased}")
    print(f"  ATP production: {atp_increased}")
    print(f"  Lactate production: {lac_increased}")
    print(f"  ROS production: {ros_increased}")
    print(f"  pH decrease: {ph_decreased}")
    print(f"  Stress increase: {stress_increased}")
    print(f"  RESULT: {'PASS' if passed else 'FAIL'}")
    return passed


if __name__ == "__main__":
    sys.exit(0 if test_metabolism() else 1)