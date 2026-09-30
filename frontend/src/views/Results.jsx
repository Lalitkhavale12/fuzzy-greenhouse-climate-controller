import {
  CartesianGrid,
  ComposedChart,
  Legend,
  Line,
  ResponsiveContainer,
  Scatter,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { api } from "../api";
import { Card, useApi } from "../common";

export default function Results() {
  const [rows, rowsErr] = useApi(api.scoreboard, []);
  const [verdict] = useApi(api.verdict, []);
  const [pareto] = useApi(api.pareto, []);

  return (
    <>
      {rowsErr && <p className="err">{rowsErr}</p>}
      {rows && (
        <Card title="Scoreboard (results/comparison.csv, 8 rows)">
          <table className="data">
            <thead>
              <tr>
                <th>controller</th>
                <th>weather</th>
                <th>iae_T</th>
                <th>iae_H</th>
                <th>energy</th>
                <th>cost</th>
                <th>rank</th>
              </tr>
            </thead>
            <tbody>
              {rows.map((r, i) => (
                <tr key={i}>
                  <td>{r.controller}</td>
                  <td>{r.weather}</td>
                  <td>{r.iae_T}</td>
                  <td>{r.iae_H}</td>
                  <td>{r.energy}</td>
                  <td>{r.cost}</td>
                  <td>{r.rank}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </Card>
      )}
      {verdict && (
        <Card title="Holdout verdict">
          <pre className="verdict">{verdict.text}</pre>
        </Card>
      )}
      {pareto && (
        <Card title="Energy vs comfort — holdout Pareto">
          <ResponsiveContainer width="100%" height={300}>
            <ComposedChart>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="energy" type="number" label={{ value: "energy", position: "insideBottomRight" }} />
              <YAxis dataKey="discomfort" type="number" label={{ value: "discomfort", angle: -90 }} />
              <Tooltip cursor={{ strokeDasharray: "3 3" }} />
              <Legend />
              <Scatter name="controllers" data={pareto.points} fill="#78909C" />
              <Line name="frontier" data={pareto.frontier} dataKey="discomfort" stroke="#F59E0B" strokeDasharray="5 4" dot={false} />
            </ComposedChart>
          </ResponsiveContainer>
        </Card>
      )}
      <Card title="Evidence pack">
        <a href={api.evidenceUrl} download>
          Download evidence pack (ZIP)
        </a>
      </Card>
    </>
  );
}
