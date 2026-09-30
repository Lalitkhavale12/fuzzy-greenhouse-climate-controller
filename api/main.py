"""FastAPI backend over the frozen src/ engine (React UI stack).

Read-only: frozen results//weather/ are never written; non-7/21 seeds use
ephemeral synthetic weather. Mirrors exactly what the Streamlit pages need,
so the React frontend is a thin view layer like dashboard/ is.

Run:  uvicorn api.main:app --port 8000  (from repo root)
"""

import functools
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import numpy as np
import matplotlib
matplotlib.use("Agg")  # headless server: never open a GUI backend
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response
from pydantic import BaseModel, Field

from src.greenhouse_model import step, load_weather_profile, daytime_solar, params
from src.metrics import run_closed_loop, all_metrics
from src.onoff_controller import onoff_step
from src.pid_controller import pid_step
from src.fuzzy_controller import fuzzy_step
from src.ga_fuzzy_controller import ga_fuzzy_step
from src.adaptive_fuzzy import adaptive_fuzzy_step
from dashboard.helpers import (load_kpi_row, scoreboard_rows, verdict_text,
                               evidence_zip_bytes, mf_sensitivity_costs,
                               robustness_table, pareto_frontier,
                               ephemeral_weather_path, DISPLAY)

STEPS = {"onoff": onoff_step,
         "pid": functools.partial(pid_step, dt=60.0),
         "fuzzy": functools.partial(fuzzy_step, dt=60.0),
         "ga_fuzzy": functools.partial(ga_fuzzy_step, dt=60.0),
         "adaptive": adaptive_fuzzy_step}
T_INIT_C, W_INIT = 29.28, 20.0  # probe-verified baseline initial condition

app = FastAPI(title="Greenhouse Climate API")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)


def _weather(seed: int) -> str:
    if seed == 7:
        return "weather/weather_profile.csv"
    if seed == 21:
        return "weather/holdout_21.csv"
    return ephemeral_weather_path(seed)


class ClosedLoopReq(BaseModel):
    controller: str = "ga_fuzzy"
    T_sp: float = Field(25.0, ge=10.0, le=35.0)
    RH_sp: float = Field(70.0, ge=30.0, le=100.0)
    seed: int = Field(7, ge=1, le=50)
    n: int = Field(1440, ge=60, le=1440)


class OpenLoopReq(BaseModel):
    heater: float = Field(0.8, ge=0.0, le=1.0)
    fan: float = Field(0.0, ge=0.0, le=1.0)
    fogger: float = Field(0.5, ge=0.0, le=1.0)
    vent: float = Field(0.25, ge=0.0, le=1.0)
    seed: int = Field(7, ge=1, le=50)


class SensitivityReq(BaseModel):
    delta: float = Field(0.5, gt=0.0, le=2.0)
    n: int = Field(1440, ge=60, le=1440)


@app.get("/api/health")
def health():
    return {"status": "ok", "controllers": sorted(STEPS)}


@app.get("/api/kpi")
def kpi():
    try:
        return dict(load_kpi_row())
    except (OSError, ValueError, AssertionError, KeyError) as exc:
        raise HTTPException(500, "frozen scoreboard unreadable: %s" % exc)


@app.get("/api/scoreboard")
def scoreboard():
    try:
        return scoreboard_rows()
    except (OSError, ValueError) as exc:
        raise HTTPException(500, "frozen scoreboard unreadable: %s" % exc)


@app.get("/api/verdict")
def verdict():
    try:
        return {"text": verdict_text(scoreboard_rows())}
    except (OSError, ValueError) as exc:
        raise HTTPException(500, "frozen scoreboard unreadable: %s" % exc)


@app.get("/api/artifact")
def artifact():
    import json
    try:
        with open("results/ga_optimized_params.json") as f:
            return json.load(f)
    except (OSError, ValueError) as exc:
        raise HTTPException(500, "frozen GA artifact unreadable: %s" % exc)


@app.get("/api/pareto")
def pareto():
    try:
        pts, front = pareto_frontier()
    except (OSError, ValueError) as exc:
        raise HTTPException(500, "pareto failed: %s" % exc)
    return {"points": [{"energy": e, "discomfort": d, "label": lab}
                       for e, d, lab in pts],
            "frontier": [{"energy": e, "discomfort": d, "label": lab}
                         for e, d, lab in front]}


@app.get("/api/evidence.zip")
def evidence_zip():
    try:
        data = evidence_zip_bytes()
    except (OSError, ValueError) as exc:
        raise HTTPException(500, "evidence pack failed: %s" % exc)
    return Response(data, media_type="application/zip",
                    headers={"Content-Disposition":
                             "attachment; filename=greenhouse_evidence_pack.zip"})


@app.post("/api/open-loop")
def open_loop(req: OpenLoopReq):
    t_min, T_out, w_out = load_weather_profile(_weather(req.seed))
    hours = (np.arange(0, 1440) / 60.0).tolist()
    T_out_hr = np.interp(hours, t_min, T_out).tolist()
    w_out_hr = np.interp(hours, t_min, w_out).tolist()
    act = {"heater": req.heater, "fan_cooler": req.fan,
           "fogger": req.fogger, "vent": req.vent}
    T, w = T_INIT_C, W_INIT
    T_tr, rh_tr = [], []
    for i, h in enumerate(hours):
        ws = (T_out_hr[i], w_out_hr[i], daytime_solar(h, params["A_sol"]))
        T, w, rh = step(60.0, act, ws, T, w)
        T_tr.append(T)
        rh_tr.append(rh)
    return {"hours": hours, "T": T_tr, "rh": rh_tr, "T_out": T_out_hr}


@app.post("/api/closed-loop")
def closed_loop(req: ClosedLoopReq):
    fn = STEPS.get(req.controller)
    if fn is None:
        raise HTTPException(400, "unknown controller: %s" % req.controller)
    T, RH, U = run_closed_loop(fn, _weather(req.seed), n=req.n,
                               T_sp=req.T_sp, RH_sp=req.RH_sp)
    m = all_metrics(T, RH, U, req.T_sp, req.RH_sp)
    sat = sum(1 for u in U
              if u["heater"] >= 0.99 or u["fan_cooler"] >= 0.99)
    return {"hours": (np.arange(0, req.n) / 60.0).tolist(), "T": T, "RH": RH,
            "metrics": {k: (v if np.isfinite(v) else None)
                        for k, v in m.items() if k != "settling_min"},
            "settling_min": (m["settling_min"]
                             if np.isfinite(m["settling_min"]) else None),
            "sat_pct": round(100.0 * sat / max(1, len(U)), 1),
            "display": DISPLAY.get(req.controller, req.controller)}


@app.post("/api/sensitivity")
def sensitivity(req: SensitivityReq):
    base, rows = mf_sensitivity_costs(delta=req.delta, n=req.n)
    return {"base": base,
            "rows": [{"param": lab, "dcost": dc} for lab, dc in rows]}


@app.post("/api/robustness")
def robustness(n: int = 1440):
    if not 60 <= n <= 1440:
        raise HTTPException(400, "n must be within [60, 1440]")
    return robustness_table(n=n)
