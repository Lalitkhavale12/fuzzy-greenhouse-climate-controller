import { useState } from "react";
import Plot from "react-plotly.js";
import { DISPLAY, api } from "../api";
import { Card, Slider, meanLast, useApi } from "../common";

const L = 10.0;
const W = 6.0;
const H = 3.0;
const XS = [1.5, 4.17, 6.83, 8.5];
const YS = [1.2, 3.0, 4.8];

function solarAt(hour) {
  // Mirrors src/greenhouse_model.py daytime_solar with A_sol = 100.
  if (hour < 6 || hour > 18) return 0;
  return 100 * Math.sin((Math.PI * (hour - 6)) / 12);
}

function healthOf(tMean, rhMean, tsp, rhsp, x) {
  // House mean + illustrative +/-1 C vent-to-wall gradient, mapped 0..1.
  const off = (x / L - 0.5) * 2.0;
  return Math.min(1, Math.max(0, 1 - Math.abs(tMean + off - tsp) / 10 - Math.abs(rhMean - rhsp) / 40));
}

function houseEdges() {
  const c = [];
  for (const x of [0, L])
    for (const y of [0, W]) for (const z of [0, H]) c.push([x, y, z]);
  const e = [[0, 1], [0, 2], [1, 3], [2, 3], [4, 5], [4, 6], [5, 7], [6, 7], [0, 4], [1, 5], [2, 6], [3, 7]];
  const x = [];
  const y = [];
  const z = [];
  for (const [a, b] of e) {
    x.push(c[a][0], c[b][0], null);
    y.push(c[a][1], c[b][1], null);
    z.push(c[a][2], c[b][2], null);
  }
  return { x, y, z };
}

export default function PlantHouse() {
  const [tsp, setTsp] = useState(25.0);
  const [rhsp, setRhsp] = useState(70);
  const [ctl, setCtl] = useState("ga_fuzzy");
  const [seed, setSeed] = useState(7);
  const [hour, setHour] = useState(12);
  const [pick, setPick] = useState(1);
  const [sim, err] = useApi(
    () => api.closedLoop({ controller: ctl, T_sp: tsp, RH_sp: rhsp, seed }),
    [ctl, tsp, rhsp, seed]
  );

  let fig = null;
  let meanH = 0;
  let healths = [];
  if (sim) {
    const tMean = meanLast(sim.T);
    const rhMean = meanLast(sim.RH);
    const growth = 0.25 + (0.75 * hour) / 24;
    const grid = [];
    for (const x of XS) for (const y of YS) grid.push([x, y]);
    healths = grid.map(([x]) => healthOf(tMean, rhMean, tsp, rhsp, x));
    meanH = healths.reduce((a, b) => a + b, 0) / healths.length;
    const edges = houseEdges();
    const sx = [];
    const sy = [];
    const sz = [];
    const cx = [];
    const cy = [];
    const cz = [];
    const sizes = [];
    const colors = [];
    grid.forEach(([x, y], i) => {
      const h = healths[i];
      const stem = (0.6 + 1.6 * h) * growth;
      sx.push(x, x, null);
      sy.push(y, y, null);
      sz.push(0, stem, null);
      cx.push(x);
      cy.push(y);
      cz.push(stem + 0.15);
      sizes.push(8 + 14 * h);
      const r = Math.round(121 + (46 - 121) * h);
      const g = Math.round(85 + (125 - 85) * h);
      const b = Math.round(72 + (50 - 72) * h);
      colors.push(`rgb(${r},${g},${b})`);
    });
    fig = {
      data: [
        { x: edges.x, y: edges.y, z: edges.z, mode: "lines", type: "scatter3d", line: { color: "#2E7D32", width: 4 }, name: "house" },
        { x: sx, y: sy, z: sz, mode: "lines", type: "scatter3d", line: { color: "#33691E", width: 5 }, name: "stems" },
        { x: cx, y: cy, z: cz, mode: "markers", type: "scatter3d", marker: { size: sizes, color: colors }, name: "canopy" },
      ],
      layout: {
        title: `Greenhouse crop — hour ${hour}, mean health ${meanH.toFixed(2)}`,
        showlegend: false,
        margin: { l: 0, r: 0, t: 30, b: 0 },
        scene: { aspectmode: "manual", aspectratio: { x: 10 / 3, y: 2, z: 1 }, xaxis: { visible: false }, yaxis: { visible: false }, zaxis: { visible: false } },
      },
    };
  }

  return (
    <>
      <Card title="Climate + time">
        <div className="controls">
          <Slider label="T setpoint" min={18} max={30} step={0.5} value={tsp} set={setTsp} />
          <Slider label="RH setpoint" min={50} max={90} step={1} value={rhsp} set={setRhsp} />
          <label>
            controller:{" "}
            <select value={ctl} onChange={(e) => setCtl(e.target.value)}>
              {Object.keys(DISPLAY).map((k) => (
                <option key={k} value={k}>
                  {DISPLAY[k]}
                </option>
              ))}
            </select>
          </label>
          <Slider label="seed" min={1} max={50} step={1} value={seed} set={setSeed} />
          <Slider label="hour" min={0} max={23} step={1} value={hour} set={setHour} />
        </div>
      </Card>
      {err && <p className="err">{err}</p>}
      {sim && (
        <>
          <div className="kpis">
            <div className="kpi">
              <small>mean crop health</small>
              <div>{meanH.toFixed(2)}</div>
            </div>
            <div className="kpi">
              <small>solar at hour {hour}</small>
              <div>{solarAt(hour).toFixed(0)} W/m2</div>
            </div>
            <div className="kpi">
              <small>
                plant {pick} health
                <br />
                <select value={pick} onChange={(e) => setPick(Number(e.target.value))}>
                  {healths.map((_, i) => (
                    <option key={i + 1} value={i + 1}>
                      plant {i + 1}
                    </option>
                  ))}
                </select>
              </small>
              <div>{healths[pick - 1].toFixed(2)}</div>
            </div>
          </div>
          <Card title="3D greenhouse">
            <Plot data={fig.data} layout={fig.layout} style={{ width: "100%" }} useResizeHandler />
          </Card>
        </>
      )}
    </>
  );
}
