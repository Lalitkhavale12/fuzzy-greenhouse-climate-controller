"""Simulated greenhouse plant — coupled energy + moisture ODEs (MODEL-01).

Verbatim-core copy of RESEARCH.md Pattern 1 (probe-verified 2026-09-20,
numpy 2.4.3). State: T (degC), w (g/kg absolute humidity), per m3 of
greenhouse volume. Integration is fixed forward Euler (D-13, locked) with
the non-oscillatory stability gate asserted per step; the locked dt=60s has
12x margin on the moisture exchange rate (Pitfall 1).

Pure and stateless (D-15): the caller owns the state and passes it in/out —
the same function drives the controllers, the GA fitness loop, and the
notebooks, with no duplicated logic (PROJECT.md).
"""

import numpy as np

params = {                          # D-07 named dict — all values probe-verified
    "C_vol": 1.8e4,                 # J/(m3·K) effective volumetric heat capacity (air+structure)
    "U_env": 5.0,                   # W/(m3·K) envelope conduction (≈8 W/m2K glass, A/V≈0.7)
    "P_h":   100.0,                 # W/m3    heater sensible heat at duty 1.0
    "P_fan": 200.0,                 # W/m3    fan/cooler heat extraction at duty 1.0
    "P_fog": 20.0,                  # W/m3    fogger evaporative cooling at duty 1.0
    "m_fog": 7.4e-3,                # g/(kg·s) fogger moisture injection (≈0.44 g/kg/min)
    "ACH":   4.5,                   # air changes/hour — natural vent exchange rate
    "L_v":   1.508,                 # W/(m3·K) vent sensible exchange = rho·cp·ACH/3600
    "X_v":   1.25e-3,               # 1/s      vent moisture exchange = ACH/3600
    "E_base": 2.5e-3,               # g/(kg·s) base transpiration + floor evaporation (no crop)
    "k_c":   1.5e-4,                # 1/s      cooler condensation dehumidification (w>wsat only)
    "A_sol": 100.0,                 # W/m3     daytime solar gain peak, 06:00–18:00 [ASSUMED addition]
}


def es_pa(T_C: float) -> float:
    """Saturation vapor pressure (Pa) — Alduchov & Eskridge 1996 Magnus form."""
    return 610.94 * np.exp(17.625 * T_C / (T_C + 243.04))


def wsat_g_per_kg(T_C: float, p_Pa: float = 101325.0) -> float:
    """Saturation absolute humidity (g/kg) at sea level."""
    return 622.0 * es_pa(T_C) / (p_Pa - es_pa(T_C))


def relative_humidity(w_g_per_kg: float, T_C: float) -> float:
    """RH (%) = w/wsat(T)*100, clamped to [0, 100] (D-16; Pitfall 2)."""
    rh = 100.0 * w_g_per_kg / wsat_g_per_kg(T_C)
    return float(min(max(rh, 0.0), 100.0))


def daytime_solar(t_hour: float, A_sol: float) -> float:
    """Sine solar gain 06:00–18:00 local, peak A_sol W/m3 at noon, else 0."""
    if 6.0 <= t_hour <= 18.0:
        return A_sol * np.sin(np.pi * (t_hour - 6.0) / 12.0)
    return 0.0


def step(dt: float, actuators: dict, weather_at_t: tuple,
         T_C: float, w_gkg: float) -> tuple[float, float, float]:
    """One forward-Euler step (D-13) -> (T_C_new, w_new, rh_pct).

    actuators: exactly {"heater","fan_cooler","fogger","vent"} with duties in
        [0,1] (fail-fast asserts — no other key set is accepted).
    weather_at_t: (T_out_degC, w_out_gkg, solar_Wm3).
    """
    expected = {"heater", "fan_cooler", "fogger", "vent"}
    assert set(actuators) == expected, f"actuator keys must be exactly {expected}"
    for duty in actuators.values():
        assert 0.0 <= duty <= 1.0, "actuator duties must lie in [0, 1]"
    assert (params["X_v"] + params["k_c"]) * dt < 1, \
        "forward Euler non-oscillatory gate: (X_v + k_c)*dt must be < 1"

    T_out, w_out, sol = weather_at_t
    u_h, u_c, u_f, u_v = (actuators["heater"], actuators["fan_cooler"],
                          actuators["fogger"], actuators["vent"])

    dT = (params["P_h"]*u_h - params["P_fan"]*u_c - params["P_fog"]*u_f + sol
          + (params["U_env"] + params["L_v"]*u_v) * (T_out - T_C)) / params["C_vol"]
    T_new = T_C + dT * dt

    cond = params["k_c"] * u_c * max(w_gkg - wsat_g_per_kg(T_new), 0.0)  # supersaturation only
    w_new = w_gkg + (params["E_base"] + params["m_fog"]*u_f
                     + params["X_v"]*u_v * (w_out - w_gkg) - cond) * dt
    w_new = min(w_new, wsat_g_per_kg(T_new))          # Pitfall 2: excess condenses

    assert np.isfinite(T_new) and np.isfinite(w_new)
    assert abs(T_new) < 1e3
    return T_new, w_new, relative_humidity(w_new, T_new)


def load_weather_profile(path: str) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Load weather CSV -> (t_minutes, temp_C, w_out_gkg).

    Space-delimited numeric rows (D-13) after the header line
    "time_min,temp_C,rh_pct". Validates monotonic integer minutes with
    endpoints 0..1440 and RH in [0,100]; derives w_out from RH + T via
    wsat() so the plant reads absolute humidity (D-10).
    """
    arr = np.loadtxt(path, skiprows=1)
    t_min, temp_C, rh_pct = arr[:, 0], arr[:, 1], arr[:, 2]
    assert np.all(np.diff(t_min) > 0), "time column must be strictly increasing"
    assert t_min[0] == 0.0 and t_min[-1] == 1440.0, "time must span 0..1440 min"
    assert np.all((rh_pct >= 0.0) & (rh_pct <= 100.0)), "RH must lie in [0, 100]"
    w_out = rh_pct / 100.0 * wsat_g_per_kg(temp_C)
    return t_min, temp_C, w_out


C_OUT_PPM = 420.0  # outdoor CO2 baseline
Q_CO2 = 0.5  # ppm/s injection at co2_valve duty 1.0
K_LEAK = 2.0e-4  # 1/s passive house leakage toward outdoor
C_LO, C_HI = 300.0, 2000.0  # display/validity clamp band


def step_co2(dt: float, actuators: dict, weather_at_t: tuple,
             T_C: float, w_gkg: float, C_ppm: float
             ) -> tuple[float, float, float, float]:
    """step() plus a CO2 valve state (Claim 1 fifth actuator).

    Thermal/moisture core is untouched: the 4-key subset goes to step()
    verbatim, so 4-key behavior is bit-identical. CO2 accumulates by valve
    injection and flushes by vent exchange + passive leak toward C_OUT_PPM.
    Closed-loop controllers do not dose CO2 (documented); the valve is
    operated open-loop (Model Sim) or as a dosed level (Plant House).
    """
    assert set(actuators) == {"heater", "fan_cooler", "fogger", "vent",
                              "co2_valve"}, \
        f"CO2 wrapper needs all five actuator keys, got {set(actuators)}"
    assert all(np.isfinite(v) and 0.0 <= v <= 1.0
               for v in actuators.values()), "duties in [0,1]"
    assert np.isfinite(C_ppm)
    core = {k: actuators[k]
            for k in ("heater", "fan_cooler", "fogger", "vent")}
    T_new, w_new, rh = step(dt, core, weather_at_t, T_C, w_gkg)
    u_c, u_v = actuators["co2_valve"], actuators["vent"]
    vent_rate = params["X_v"] * u_v
    C_new = C_ppm + (Q_CO2 * u_c
                     - (vent_rate + K_LEAK) * (C_ppm - C_OUT_PPM)) * dt
    assert np.isfinite(C_new)
    return T_new, w_new, rh, float(min(max(C_new, C_LO), C_HI))