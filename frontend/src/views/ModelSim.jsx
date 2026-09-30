import { useState } from "react";
import {
  CartesianGrid,
  Legend,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { api } from "../api";
import { Card, Slider, thin, useApi } from "../common";

export default function ModelSim() {
  const [heater, setHeater] = useStateFn(0.8);
  const [fan, setFan] = useStateFn(0.0);
  const [fogger, setFogger] = useStateFn(0.5);
  const [vent, setVent] = useStateFn(0.25);
  const [seed, setSeed] = useStateFn(7);
  const [sim, err] = useApi(
    () => api.openLoop({ heater, fan, fogger, vent, seed }),
    [heater, fan, fogger, vent, seed]
  );

  return (
    <>
      <Card title="Duties + weather">
        <div className="controls">
          <Slider label="heater" min={0} max={1} step={0.05} value={heater} set={setHeater} />
          <Slider label="fan/cooler" min={0} max={1} step={0.05} value={fan} set={setFan} />
          <Slider label="fogger" min={0} max={1} step={0.05} value={fogger} set={setFogger} />
          <Slider label="vent" min={0} max={1} step={0.05} value={vent} set={setVent} />
          <Slider label="weather seed" min={1} max={50} step={1} value={seed} set={setSeed} />
        </div>
      </Card>
      {err && <p className="err">{err}</p>}
      {sim && (
        <>
          <Card title="Inside temperature (24 h open-loop)">
            <ResponsiveContainer width="100%" height={300}>
              <LineChart
                data={thin(sim.hours).map((h, i) => ({
                  h: +h.toFixed(1),
                  inside: sim.T[i * 5],
                  outside: sim.T_out[i * 5],
                }))}
              >
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="h" label={{ value: "hour", position: "insideBottomRight" }} />
                <YAxis />
                <Tooltip />
                <Legend />
                <Line type="monotone" dataKey="inside" stroke="#1E40AF" dot={false} />
                <Line type="monotone" dataKey="outside" stroke="#78909C" strokeDasharray="5 5" dot={false} />
              </LineChart>
            </ResponsiveContainer>
          </Card>
          <Card title="Relative humidity">
            <ResponsiveContainer width="100%" height={220}>
              <LineChart
                data={thin(sim.hours).map((h, i) => ({ h: +h.toFixed(1), rh: sim.rh[i * 5] }))}
              >
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="h" />
                <YAxis domain={[0, 100]} />
                <Tooltip />
                <Line type="monotone" dataKey="rh" stroke="#3B82F6" dot={false} />
              </LineChart>
            </ResponsiveContainer>
            <p className="muted">
              Inside T [{Math.min(...sim.T).toFixed(2)}, {Math.max(...sim.T).toFixed(2)}] C · RH [
              {Math.min(...sim.rh).toFixed(1)}, {Math.max(...sim.rh).toFixed(1)}] %
            </p>
          </Card>
        </>
      )}
    </>
  );
}

function useStateFn(init) {
  const [v, set] = useState(init);
  return [v, set];
}
