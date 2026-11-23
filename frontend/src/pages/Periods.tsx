import { useCallback, useEffect, useState } from "react";
import { api, ApiError, type Period } from "../api";
import { useAuth } from "../auth";
import { monthName } from "../money";

export default function Periods() {
  const { user } = useAuth();
  const [periods, setPeriods] = useState<Period[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [year, setYear] = useState(() => new Date().getFullYear());
  const [month, setMonth] = useState(() => new Date().getMonth() + 1);

  const load = useCallback(async () => {
    try {
      setPeriods(await api.periods.list());
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Could not load periods.");
    }
  }, []);

  useEffect(() => {
    void load();
  }, [load]);

  async function run(fn: () => Promise<unknown>) {
    setError(null);
    try {
      await fn();
      await load();
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Request failed.");
    }
  }

  return (
    <>
      <h1>Period close</h1>
      <p className="muted" style={{ maxWidth: 640 }}>
        Closing a month locks every entry dated in it. Nothing can be posted, cancelled or reversed
        into a closed month; corrections go in the current month. Months close in order. Only the
        owner can reopen, and only the most recent closed month.
      </p>
      {error && <div className="error">{error}</div>}

      <div className="card" style={{ maxWidth: 480 }}>
        <div className="row">
          <div className="field">
            <label htmlFor="y">Year</label>
            <input id="y" type="number" value={year} onChange={(e) => setYear(Number(e.target.value))} />
          </div>
          <div className="field">
            <label htmlFor="m">Month</label>
            <select id="m" value={month} onChange={(e) => setMonth(Number(e.target.value))}>
              {Array.from({ length: 12 }, (_, i) => i + 1).map((m) => (
                <option key={m} value={m}>
                  {monthName(m)}
                </option>
              ))}
            </select>
          </div>
        </div>
        <button onClick={() => run(() => api.periods.close(year, month))}>Close month</button>
      </div>

      <h2>Closed months</h2>
      <table style={{ maxWidth: 480 }}>
        <thead>
          <tr>
            <th>Month</th>
            <th>Status</th>
            {user?.role === "owner" && <th></th>}
          </tr>
        </thead>
        <tbody>
          {periods.map((p) => (
            <tr key={`${p.year}-${p.month}`}>
              <td>
                {monthName(p.month)} {p.year}
              </td>
              <td>{p.closed ? "Closed" : "Open"}</td>
              {user?.role === "owner" && (
                <td>
                  {p.closed && (
                    <button className="secondary" onClick={() => run(() => api.periods.reopen(p.year, p.month))}>
                      Reopen
                    </button>
                  )}
                </td>
              )}
            </tr>
          ))}
          {periods.length === 0 && (
            <tr>
              <td colSpan={3} className="muted">
                No month has been closed yet.
              </td>
            </tr>
          )}
        </tbody>
      </table>
    </>
  );
}
