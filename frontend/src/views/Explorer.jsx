import { useState } from "react";
import {
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  Legend,
  Line,
  LineChart,
  ReferenceLine,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { api } from "../api";
import { Card, Slider, useApi } from "../common";

function tri(x, c, w) {
  return Math.max(0, 1 - Math.abs(x - c) / w);
}

const GROUPS = ["eT", "eH", "deT", "du", "deH", "dv"];

export default function Explorer() {
  const [art, artErr] = useApi(api.artifact, []);
  const [gen, setGen] = useState(50);
  const [group, setGroup] = useState("eT");
  const [sens, setSens] = useState(null);
  const [sensErr, setSensErr] = useState(null);

  return (
    <>
      {artErr && <p className="err">{artErr}</p>}
      {art && (
        <>
          <div className="kpis">
            <div className="kpi">
              <small>train fitness</small>
              <div>{art.fitness.toFixed(2)}</div>
            </div>
            <div className="kpi">
              <small>coupling k_heat</small>
              <div>{art.coupling.k_heat.toFixed(3)}</div>
            </div>
            <div className="kpi">
              <small>coupling k_vent</small>
              <div>{art.coupling.k_vent.toFixed(3)}</div>
            </div>
            <div className="kpi">
              <small>generations</small>
              <div>{art.generations}</div>
            </div>
          </div>
          <Card title="Convergence (50 generations)">
            <ResponsiveContainer width="100%" height={260}>
              <LineChart
                data={art.history.best.map((b, i) => ({
                  gen: i + 1,
                  best: b,
                  mean: art.history.mean[i],
                }))}
              >
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="gen" />
                <YAxis />
                <Tooltip />
                <Legend />
                <Line type="monotone" dataKey="best" stroke="#1E40AF" dot={false} />
                <Line type="monotone" dataKey="mean" stroke="#78909C" dot={false} />
              </LineChart>
            </ResponsiveContainer>
          </Card>
          <Card title="Convergence replay">
            <Slider label="generation" min={1} max={50} step={1} value={gen} set={setGen} />
            <p>
              gen {gen}/50 · best {art.history.best[gen - 1].toFixed(2)}
            </p>
            <ResponsiveContainer width="100%" height={220}>
              <LineChart
                data={art.history.best.map((b, i) => ({ gen: i + 1, best: b }))}
              >
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="gen" />
                <YAxis />
                <Tooltip />
                <Line type="monotone" dataKey="best" stroke="#1E40AF" dot={false} />
                <ReferenceLine x={gen} stroke="#263023" strokeDasharray="4 4" />
              </LineChart>
            </ResponsiveContainer>
          </Card>
          <Card title="Membership before/after (hand solid vs GA dashed)">
            <div className="controls">
              <label>
                group:{" "}
                <select value={group} onChange={(e) => setGroup(e.target.value)}>
                  {GROUPS.map((g) => (
                    <option key={g} value={g}>
                      {g}
                    </option>
                  ))}
                </select>
              </label>
            </div>
            <MFOverlay group={group} art={art} />
          </Card>
        </>
      )}
      <Card title="MF sensitivity">
        {!sens ? (
          <button
            className="run"
            onClick={() =>
              api
                .sensitivity({ delta: 0.5 })
                .then(setSens)
                .catch((e) => setSensErr(String(e)))
            }
          >
            Run sensitivity (10 closed-loop runs)
          </button>
        ) : (
          <>
            <p className="muted">hand-fuzzy baseline cost: {sens.base.toFixed(2)} (seed 7)</p>
            <ResponsiveContainer width="100%" height={300}>
              <BarChart data={sens.rows} layout="vertical">
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis type="number" />
                <YAxis dataKey="param" type="category" width={80} />
                <Tooltip />
                <Bar dataKey="dcost">
                  {sens.rows.map((r, i) => (
                    <Cell key={i} fill={r.dcost > 0 ? "#C62828" : "#2E7D32"} />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </>
        )}
        {sensErr && <p className="err">{sensErr}</p>}
      </Card>
    </>
  );
}

function MFOverlay({ group, art }) {
  // Hand MFs are frozen constants mirrored from src/fuzzy_controller.py.
  const HAND = {
    eT: { c: [-4, -2, 0, 2, 4], w: [2, 2, 2, 2, 2] },
    deT: { c: [-0.5, -0.25, 0, 0.25, 0.5], w: [0.25, 0.25, 0.25, 0.25, 0.25] },
    du: { c: [-0.1, -0.05, 0, 0.05, 0.1], w: [0.05, 0.05, 0.05, 0.05, 0.05] },
    eH: { c: [-30, -15, 0, 15, 30], w: [15, 15, 15, 15, 15] },
    deH: { c: [-6, -3, 0, 3, 6], w: [3, 3, 3, 3, 3] },
    dv: { c: [-0.1, -0.05, 0, 0.05, 0.1], w: [0.05, 0.05, 0.05, 0.05, 0.05] },
  };
  const hand = HAND[group];
  const opt = art.mfs[group];
  const lo = Math.min(...hand.c, ...opt.centers) - Math.max(...hand.w, ...opt.widths);
  const hi = Math.max(...hand.c, ...opt.centers) + Math.max(...hand.w, ...opt.widths);
  const data = [];
  for (let i = 0; i <= 80; i++) {
    const x = lo + ((hi - lo) * i) / 80;
    const row = { x: +x.toFixed(3) };
    hand.c.forEach((c, j) => {
      row[`hand${j}`] = tri(x, c, hand.w[j]);
    });
    opt.centers.forEach((c, j) => {
      row[`ga${j}`] = tri(x, c, opt.widths[j]);
    });
    data.push(row);
  }
  return (
    <ResponsiveContainer width="100%" height={260}>
      <LineChart data={data}>
        <CartesianGrid strokeDasharray="3 3" />
        <XAxis dataKey="x" />
        <YAxis domain={[0, 1]} />
        <Tooltip />
        {hand.c.map((_, j) => (
          <Line key={`h${j}`} type="monotone" dataKey={`hand${j}`} stroke="#1E40AF" dot={false} strokeOpacity={0.6} />
        ))}
        {opt.centers.map((_, j) => (
          <Line
            key={`g${j}`}
            type="monotone"
            dataKey={`ga${j}`}
            stroke="#F59E0B"
            strokeDasharray="5 4"
            dot={false}
          />
        ))}
      </LineChart>
    </ResponsiveContainer>
  );
}
