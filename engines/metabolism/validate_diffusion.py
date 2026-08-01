# validate_diffusion.py
"""
Validation of diffusion behaviour.

Tests:
- Diffusion reduces concentration gradients.
- Vascular supply regions remain fixed.
- No NaN or Inf values.
- No negative concentrations.
- Numerical stability over many iterations.
"""

import sys
import numpy as np
from engine import SimulationConfig, MetabolismEngine


def test_diffusion():
    # Use a configuration with zero consumption/production to isolate diffusion.
    cfg = SimulationConfig(
        random_seed=42,
        time_steps=20,
        dt=0.1,
        num_regions=10,
        vascular_density=0.2,          # some vascular regions
        vascular_supply_oxygen=1.0,
        vascular_supply_glucose=1.0,
        diffusion_oxygen=0.1,
        diffusion_glucose=0.08,
        diffusion_lactate=0.05,
        diffusion_ph=0.02,
        oxygen_consumption_rate=0.0,    # no consumption
        glucose_consumption_rate=0.0,
        glycolytic_atp_yield=0.0,
        oxidative_atp_yield=0.0,
        lactate_production_rate=0.0,
        warburg_bias=0.0,
        aerobic_glycolysis_fraction=0.0,
        mitochondrial_efficiency_base=1.0,
        initial_ph=7.4,
        ph_acidification_rate=0.0,
        ph_buffering=0.0,
        ros_production_rate=0.0,
        ros_decay_rate=0.0,
        development_mode=False,
        strict_validation=False,       # skip validation for performance
        initial_oxygen=0.5,
        initial_glucose=0.5,
        initial_lactate=0.1,
        initial_atp=0.0,
    )
    eng = MetabolismEngine(cfg)
    eng.initialize_state()
    # Create a sharp gradient: set first half to high, second half to low.
    n = cfg.num_regions
    mid = n // 2
    eng.oxygen[:mid] = 1.0
    eng.oxygen[mid:] = 0.0
    eng.glucose[:mid] = 1.0
    eng.glucose[mid:] = 0.0
    eng.lactate[:mid] = 0.0
    eng.lactate[mid:] = 1.0
    # Store initial gradients (max difference)
    initial_grad_oxygen = np.max(np.abs(np.diff(eng.oxygen)))
    initial_grad_glucose = np.max(np.abs(np.diff(eng.glucose)))
    initial_grad_lactate = np.max(np.abs(np.diff(eng.lactate)))

    # Record initial state for vascular check.
    vascular_supply = eng.vascular_supply.copy()

    # Run for several steps to allow diffusion.
    for _ in range(10):
        eng._step()  # private, but we can call it for validation purposes.
        # Check that no NaN/Inf and no negatives.
        for arr in [eng.oxygen, eng.glucose, eng.lactate, eng.ph, eng.ros, eng.atp]:
            if not np.all(np.isfinite(arr)):
                print("  Non-finite value detected during diffusion")
                return False
            if np.any(arr < -1e-9):
                print("  Negative value detected during diffusion")
                return False

    # Check that gradients decreased.
    final_grad_oxygen = np.max(np.abs(np.diff(eng.oxygen)))
    final_grad_glucose = np.max(np.abs(np.diff(eng.glucose)))
    final_grad_lactate = np.max(np.abs(np.diff(eng.lactate)))
    grad_decreased = (final_grad_oxygen < initial_grad_oxygen and
                      final_grad_glucose < initial_grad_glucose and
                      final_grad_lactate < initial_grad_lactate)

    # Check that vascular regions remain at supply concentration.
    vascular_ok = True
    for i in range(n):
        if vascular_supply[i] > 0:
            if not np.isclose(eng.oxygen[i], cfg.vascular_supply_oxygen, atol=1e-6):
                vascular_ok = False
                break
            if not np.isclose(eng.glucose[i], cfg.vascular_supply_glucose, atol=1e-6):
                vascular_ok = False
                break

    # Also check that concentrations remain bounded (no explosion).
    stable = (np.max(eng.oxygen) <= 1.1 and np.max(eng.glucose) <= 1.1 and
              np.max(eng.lactate) <= 1.1)

    passed = grad_decreased and vascular_ok and stable

    print("validate_diffusion")
    print(f"  Gradients decreased: {grad_decreased}")
    print(f"  Vascular supply fixed: {vascular_ok}")
    print(f"  Concentrations bounded: {stable}")
    print(f"  RESULT: {'PASS' if passed else 'FAIL'}")
    return passed


if __name__ == "__main__":
    sys.exit(0 if test_diffusion() else 1)