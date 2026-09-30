import { useState } from "react";
import {
  CartesianGrid,
  Legend,
  Line,
  LineChart,
  ReferenceLine,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { COLORS, DISPLAY, api } from "../api";
import { Card, Slider, thin, useApi } from "../common";

const CTRLS = ["onoff", "pid", "fuzzy", "ga_fuzzy"];

export default function Controllers() {
  const [tsp, setTsp] = useState(25.0);
  const [rhsp, setRhsp] = useState(70);
  const [seedA, setSeedA] = useState(7);
  const [seedB, setSeedB] = useState(21);
  const [both, err] = useApi(async () => {
    const one = (c, seed) =>
      api.closedLoop({ controller: c, T_sp: tsp, RH_sp: rhsp, seed, n: 1440 });
    const [a, b] = await Promise.all([
      Promise.all(CTRLS.map((c) => one(c, seedA))),
      Promise.all(CTRLS.map((c) => one(c, seedB))),
    ]);
    return { a, b };
  }, [tsp, rhsp, seedA, seedB]);
  const [robust, setRobust] = useState(null);
  const [robustErr, setRobustErr] = useState(null);

  let delta = null;
  let rankLine = "";
  if (both) {
    delta = CTRLS.map((c, i) => {
      const row = { controller: DISPLAY[c] };
      for (const k of ["iae_T", "iae_H", "energy", "cost"])
        row[k] = +(both.b[i].metrics[k] - both.a[i].metrics[k]).toFixed(2);
      return row;
    });
    const rank = (side) =>
      [...side]
        .sort((x, y) => x.metrics.cost - y.metrics.cost)
        .findIndex((r) => r.display === "GA fuzzy") + 1;
    rankLine = `GA still wins: side A rank ${rank(both.a)} / side B rank ${rank(
      both.b
    )}`;
  }
  const tData = both
    ? thin(both.a[0].hours).map((h, i) => {
        const row = { h: +h.toFixed(1) };
        CTRLS.forEach((c, j) => {
          row[DISPLAY[c]] = both.a[j].T[i * 5];
        });
        return row;
      })
    : [];

  return (
    <>
      <Card title="Setpoints + weather seeds">
        <div className="controls">
          <Slider label="T setpoint" min={18} max={30} step={0.5} value={tsp} set={setTsp} />
          <Slider label="RH setpoint" min={50} max={90} step={1} value={rhsp} set={setRhsp} />
          <Slider label="seed A" min={1} max={50} step={1} value={seedA} set={setSeedA} />
          <Slider label="seed B" min={1} max={50} step={1} value={seedB} set={setSeedB} />
        </div>
      </Card>
      {err && <p className="err">{err}</p>}
      {both && (
        <>
          <Card title="Overlay: all four controllers, side A">
            <ResponsiveContainer width="100%" height={300}>
              <LineChart data={tData}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="h" />
                <YAxis />
                <Tooltip />
                <Legend />
                {CTRLS.map((c) => (
                  <Line
                    key={c}
                    type="monotone"
                    dataKey={DISPLAY[c]}
                    stroke={COLORS[c]}
                    strokeWidth={c === "ga_fuzzy" ? 3 : 1.5}
                    dot={false}
                  />
                ))}
                <ReferenceLine y={tsp} stroke={COLORS.setpoint} strokeDasharray="5 5" label="setpoint" />
              </LineChart>
            </ResponsiveContainer>
          </Card>
          <Card title="Delta B-minus-A">
            <table className="data">
              <thead>
                <tr>
                  <th>controller</th>
                  <th>d_iae_T</th>
                  <th>d_iae_H</th>
                  <th>d_energy</th>
                  <th>d_cost</th>
                </tr>
              </thead>
              <tbody>
                {delta.map((r) => (
                  <tr key={r.controller}>
                    <td>{r.controller}</td>
                    <td>{r.iae_T}</td>
                    <td>{r.iae_H}</td>
                    <td>{r.energy}</td>
                    <td>{r.cost}</td>
                  </tr>
                ))}
              </tbody>
            </table>
            <p>{rankLine}</p>
          </Card>
        </>
      )}
      <Card title="Robustness: seeds + disturbances + saturation">
        {!robust ? (
          <button
            className="run"
            onClick={() =>
              api
                .robustness()
                .then(setRobust)
                .catch((e) => setRobustErr(String(e)))
            }
          >
            Run robustness (25 closed-loop runs)
          </button>
        ) : (
          <table className="data">
            <thead>
              <tr>
                <th>controller</th>
                <th>scenario</th>
                <th>cost</th>
                <th>sat %</th>
              </tr>
            </thead>
            <tbody>
              {robust.map((r, i) => (
                <tr key={i}>
                  <td>{r.controller}</td>
                  <td>{r.scenario}</td>
                  <td>{r.cost}</td>
                  <td>{r.sat_pct}</td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
        {robustErr && <p className="err">{robustErr}</p>}
      </Card>
    </>
  );
}
