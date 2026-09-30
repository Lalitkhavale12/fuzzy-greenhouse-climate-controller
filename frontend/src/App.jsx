import { useState } from "react";
import "./styles.css";
import { api } from "./api";
import { useApi } from "./common";
import ModelSim from "./views/ModelSim.jsx";
import Controllers from "./views/Controllers.jsx";
import Explorer from "./views/Explorer.jsx";
import Results from "./views/Results.jsx";
import PlantHouse from "./views/PlantHouse.jsx";

const VIEWS = [
  ["sim", "Model Sim", ModelSim],
  ["ctl", "Controllers", Controllers],
  ["ga", "GA Explorer", Explorer],
  ["res", "Results", Results],
  ["plant", "Plant House", PlantHouse],
];

function App() {
  const [page, setPage] = useState("sim");
  const [kpi] = useApi(api.kpi, []);
  const View = VIEWS.find((v) => v[0] === page)[2];

  return (
    <>
      <header className="top">
        <h1>GA-Optimized Fuzzy Greenhouse Climate Controller</h1>
        {kpi ? (
          <p>
            Headline: GA fuzzy ranks #1 on the frozen holdout — weighted cost{" "}
            {Number(kpi.cost).toFixed(2)}, beating on/off and PID.
          </p>
        ) : (
          <p>Start the API at http://localhost:8000 for live data.</p>
        )}
      </header>
      <nav className="tabs">
        {VIEWS.map(([id, label]) => (
          <button
            key={id}
            className={id === page ? "active" : ""}
            onClick={() => setPage(id)}
          >
            {label}
          </button>
        ))}
      </nav>
      <main>
        <View />
      </main>
    </>
  );
}

export default App;
