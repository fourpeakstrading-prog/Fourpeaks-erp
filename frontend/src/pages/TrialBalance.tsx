import { useEffect, useState } from "react";
import { api, ApiError, type TrialBalance as TB } from "../api";
import { omr } from "../money";

export default function TrialBalance() {
  const [asOf, setAsOf] = useState("");
  const [tb, setTb] = useState<TB | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [hideZero, setHideZero] = useState(true);

  useEffect(() => {
    api.reports
      .trialBalance(asOf || undefined)
      .then(setTb)
      .catch((err) => setError(err instanceof ApiError ? err.message : "Could not load."));
  }, [asOf]);

  const rows = tb?.rows.filter((r) => !hideZero || Number(r.debit) !== 0 || Number(r.credit) !== 0) ?? [];
  const balanced = tb ? Number(tb.total_debit) === Number(tb.total_credit) : true;

  return (
    <>
      <h1>Trial balance</h1>
      <div style={{ display: "flex", gap: 16, alignItems: "end", marginBottom: 12, flexWrap: "wrap" }}>
        <div className="field" style={{ marginBottom: 0 }}>
          <label htmlFor="asof">As of (blank for all time)</label>
          <input id="asof" type="date" value={asOf} onChange={(e) => setAsOf(e.target.value)} style={{ width: "auto" }} />
        </div>
        <label style={{ display: "inline-flex", gap: 6, alignItems: "center", marginBottom: 8 }}>
          <input type="checkbox" style={{ width: "auto" }} checked={hideZero} onChange={(e) => setHideZero(e.target.checked)} />
          Hide accounts with no balance
        </label>
      </div>
      {error && <div className="error">{error}</div>}
      {tb && (
        <table style={{ maxWidth: 820 }}>
          <thead>
            <tr>
              <th>Code</th>
              <th>Account</th>
              <th>Type</th>
              <th style={{ textAlign: "right" }}>Debit</th>
              <th style={{ textAlign: "right" }}>Credit</th>
            </tr>
          </thead>
          <tbody>
            {rows.map((r) => (
              <tr key={r.account_id}>
                <td>{r.code}</td>
                <td>{r.name}</td>
                <td className="muted">{r.type}</td>
                <td style={{ textAlign: "right" }}>{omr(r.debit, true)}</td>
                <td style={{ textAlign: "right" }}>{omr(r.credit, true)}</td>
              </tr>
            ))}
          </tbody>
          <tfoot>
            <tr style={{ fontWeight: 600 }}>
              <td colSpan={3}>Totals {balanced ? "" : "(out of balance)"}</td>
              <td style={{ textAlign: "right" }}>{omr(tb.total_debit)}</td>
              <td style={{ textAlign: "right" }}>{omr(tb.total_credit)}</td>
            </tr>
          </tfoot>
        </table>
      )}
    </>
  );
}
