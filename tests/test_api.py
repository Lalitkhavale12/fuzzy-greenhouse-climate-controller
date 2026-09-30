"""Headless FastAPI checks (React stack).

Plain-assert standalone suite in the tests/test_dashboard.py style, via
FastAPI TestClient (in-process, no server needed).

Run:  python tests/test_api.py
"""

import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _client():
    import sys
    if ROOT not in sys.path:
        sys.path.insert(0, ROOT)
    os.chdir(ROOT)
    from fastapi.testclient import TestClient
    from api.main import app
    return TestClient(app)


def test_health():
    c = _client()
    r = c.get("/api/health")
    assert r.status_code == 200, r.text
    assert r.json() == {"status": "ok", "controllers": ["adaptive", "fuzzy",
                                                        "ga_fuzzy", "onoff",
                                                        "pid"]}, r.text
    print("health ok, 5 controllers")


def test_kpi_scoreboard_verdict():
    c = _client()
    kpi = c.get("/api/kpi").json()
    assert abs(float(kpi["cost"]) - 114.28) < 0.01, kpi
    rows = c.get("/api/scoreboard").json()
    from src.metrics import COLUMNS
    assert len(rows) == 8, len(rows)
    assert list(rows[0].keys()) == COLUMNS, list(rows[0].keys())
    txt = c.get("/api/verdict").json()["text"]
    assert "ga_fuzzy" in txt, txt[:120]
    print("kpi 114.28, 8 scoreboard rows, verdict names ga_fuzzy")


def test_artifact_pareto_zip():
    c = _client()
    d = c.get("/api/artifact").json()
    assert d["schema_version"] == 2, d.get("schema_version")
    assert len(d["history"]["best"]) == 50, len(d["history"]["best"])
    p = c.get("/api/pareto").json()
    assert len(p["points"]) == 4 and len(p["frontier"]) >= 1, p
    z = c.get("/api/evidence.zip")
    assert z.content[:2] == b"PK" and len(z.content) > 1024, len(z.content)
    print("artifact v2/50 gens, pareto 4 pts, ZIP PK ok")


def test_open_loop():
    c = _client()
    r = c.post("/api/open-loop", json={}).json()
    assert len(r["T"]) == 1440 and len(r["rh"]) == 1440, len(r["T"])
    assert all(0.0 <= v <= 100.0 for v in r["rh"]), "RH bounds"
    print("open-loop 1440 pts, RH bounded")


def test_closed_loop():
    import math
    c = _client()
    r = c.post("/api/closed-loop",
               json={"controller": "ga_fuzzy", "n": 240}).json()
    assert len(r["T"]) == 240, len(r["T"])
    assert math.isfinite(r["metrics"]["cost"]), r["metrics"]
    assert r["display"] == "GA fuzzy", r["display"]
    bad = c.post("/api/closed-loop", json={"controller": "nope", "n": 240})
    assert bad.status_code == 400, bad.status_code
    print("closed-loop ga cost %.2f, unknown controller 400"
          % r["metrics"]["cost"])


def test_sensitivity_robustness():
    import math
    c = _client()
    s = c.post("/api/sensitivity", json={"n": 120}).json()
    assert math.isfinite(s["base"]) and len(s["rows"]) == 10, s
    rows = c.post("/api/robustness?n=120").json()
    assert len(rows) == 25, len(rows)
    assert {r["controller"] for r in rows} == {"on/off", "PID", "hand fuzzy",
                                              "GA fuzzy", "adaptive fuzzy"}
    print("sensitivity 10 rows, robustness 25 rows")


if __name__ == "__main__":
    import sys
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    os.chdir(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    failures = []
    for name, fn in sorted(globals().items()):
        if name.startswith("test_") and callable(fn):
            try:
                fn()
                print(f"PASS {name}")
            except Exception as exc:
                failures.append(name)
                print(f"FAIL {name}: {exc!r}")
    if failures:
        print(f"{len(failures)} check(s) failed: {failures}")
        sys.exit(1)
    print("all checks passed")
