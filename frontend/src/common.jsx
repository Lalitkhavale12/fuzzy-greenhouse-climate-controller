import { useEffect, useState } from "react";

export function useApi(fn, deps) {
  const [data, setData] = useState(null);
  const [error, setError] = useState(null);
  useEffect(() => {
    let live = true;
    setError(null);
    fn()
      .then((d) => live && setData(d))
      .catch((e) => live && setError(String(e)));
    return () => {
      live = false;
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, deps);
  return [data, error];
}

export function Slider({ label, min, max, step, value, set }) {
  return (
    <label className="slider">
      <span>
        {label}: <b>{value}</b>
      </span>
      <input
        type="range"
        min={min}
        max={max}
        step={step}
        value={value}
        onChange={(e) => set(Number(e.target.value))}
      />
    </label>
  );
}

export function Card({ title, children }) {
  return (
    <section className="card">
      {title && <h3>{title}</h3>}
      {children}
    </section>
  );
}

/** Decimate long traces for chart rendering. */
export function thin(arr, k = 5) {
  return arr.filter((_, i) => i % k === 0);
}

export function meanLast(arr, n = 360) {
  const tail = arr.slice(-n);
  return tail.reduce((a, b) => a + b, 0) / tail.length;
}
