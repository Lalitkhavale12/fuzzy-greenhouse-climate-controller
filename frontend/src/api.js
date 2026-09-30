const BASE = "http://localhost:8000";

async function req(path, opts) {
  const r = await fetch(BASE + path, opts);
  if (!r.ok) throw new Error(`${(opts && opts.method) || "GET"} ${path}: ${r.status}`);
  return r.json();
}

function post(path, body, query = "") {
  return req(path + query, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body || {}),
  });
}

export const api = {
  kpi: () => req("/api/kpi"),
  scoreboard: () => req("/api/scoreboard"),
  verdict: () => req("/api/verdict"),
  artifact: () => req("/api/artifact"),
  pareto: () => req("/api/pareto"),
  openLoop: (b) => post("/api/open-loop", b),
  closedLoop: (b) => post("/api/closed-loop", b),
  sensitivity: (b) => post("/api/sensitivity", b),
  robustness: (n = 1440) => post("/api/robustness", {}, `?n=${n}`),
  evidenceUrl: BASE + "/api/evidence.zip",
};

export const DISPLAY = {
  onoff: "on/off",
  pid: "PID",
  fuzzy: "hand fuzzy",
  ga_fuzzy: "GA fuzzy",
  adaptive: "adaptive fuzzy",
};

export const COLORS = {
  onoff: "#1E40AF",
  pid: "#3B82F6",
  fuzzy: "#60A5FA",
  ga_fuzzy: "#F59E0B",
  adaptive: "#2E7D32",
  setpoint: "#263023",
};
