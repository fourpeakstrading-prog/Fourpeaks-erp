import { useEffect, useState, type FormEvent } from "react";
import { useNavigate } from "react-router-dom";
import { api, ApiError, type Account } from "../api";
import { omr, parseAmount, today } from "../money";

interface Line {
  account_id: string;
  debit: string;
  credit: string;
  description: string;
}

const blank = (): Line => ({ account_id: "", debit: "", credit: "", description: "" });

export default function NewEntry() {
  const navigate = useNavigate();
  const [accounts, setAccounts] = useState<Account[]>([]);
  const [date, setDate] = useState(today);
  const [narration, setNarration] = useState("");
  const [lines, setLines] = useState<Line[]>([blank(), blank()]);
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  useEffect(() => {
    api.accounts.list().then(setAccounts).catch(() => setAccounts([]));
  }, []);

  const totalDebit = lines.reduce((s, l) => s + (Number(parseAmount(l.debit) ?? 0) || 0), 0);
  const totalCredit = lines.reduce((s, l) => s + (Number(parseAmount(l.credit) ?? 0) || 0), 0);
  const diff = Math.round((totalDebit - totalCredit) * 1000) / 1000;
  const balanced = diff === 0 && totalDebit > 0;

  function update(i: number, patch: Partial<Line>) {
    setLines(lines.map((l, idx) => (idx === i ? { ...l, ...patch } : l)));
  }

  async function onSubmit(e: FormEvent) {
    e.preventDefault();
    setError(null);
    const used = lines.filter((l) => l.account_id && (l.debit || l.credit));
    if (used.length < 2) {
      setError("An entry needs at least two lines with an account and an amount.");
      return;
    }
    for (const l of used) {
      if (parseAmount(l.debit) === null || parseAmount(l.credit) === null) {
        setError("Amounts must be numbers with up to three decimals.");
        return;
      }
      if (l.debit && l.credit) {
        setError("A line can have a debit or a credit, not both.");
        return;
      }
    }
    if (!balanced) {
      setError(`Debits and credits differ by ${omr(Math.abs(diff))}.`);
      return;
    }
    setBusy(true);
    try {
      await api.journal.post({
        entry_date: date,
        narration,
        lines: used.map((l) => ({
          account_id: l.account_id,
          debit: parseAmount(l.debit) ?? "0",
          credit: parseAmount(l.credit) ?? "0",
          description: l.description,
        })),
      });
      navigate("/journal");
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Could not post the entry.");
    } finally {
      setBusy(false);
    }
  }

  return (
    <>
      <h1>New manual entry</h1>
      <form onSubmit={onSubmit} noValidate>
        <div className="card" style={{ maxWidth: 960 }}>
          <div className="row">
            <div className="field">
              <label htmlFor="d">Date</label>
              <input id="d" type="date" value={date} onChange={(e) => setDate(e.target.value)} />
            </div>
            <div className="field" style={{ gridColumn: "span 2" }}>
              <label htmlFor="n">Narration</label>
              <input id="n" value={narration} onChange={(e) => setNarration(e.target.value)} />
            </div>
          </div>

          <table>
            <thead>
              <tr>
                <th style={{ width: "34%" }}>Account</th>
                <th>Description</th>
                <th style={{ width: 140, textAlign: "right" }}>Debit</th>
                <th style={{ width: 140, textAlign: "right" }}>Credit</th>
                <th style={{ width: 40 }}></th>
              </tr>
            </thead>
            <tbody>
              {lines.map((l, i) => (
                <tr key={i}>
                  <td>
                    <select
                      aria-label={`Account for line ${i + 1}`}
                      value={l.account_id}
                      onChange={(e) => update(i, { account_id: e.target.value })}
                    >
                      <option value="">Choose…</option>
                      {accounts.map((a) => (
                        <option key={a.id} value={a.id}>
                          {a.code} {a.name}
                        </option>
                      ))}
                    </select>
                  </td>
                  <td>
                    <input
                      aria-label={`Description for line ${i + 1}`}
                      value={l.description}
                      onChange={(e) => update(i, { description: e.target.value })}
                    />
                  </td>
                  <td>
                    <input
                      aria-label={`Debit for line ${i + 1}`}
                      inputMode="decimal"
                      style={{ textAlign: "right" }}
                      value={l.debit}
                      onChange={(e) => update(i, { debit: e.target.value, credit: e.target.value ? "" : l.credit })}
                    />
                  </td>
                  <td>
                    <input
                      aria-label={`Credit for line ${i + 1}`}
                      inputMode="decimal"
                      style={{ textAlign: "right" }}
                      value={l.credit}
                      onChange={(e) => update(i, { credit: e.target.value, debit: e.target.value ? "" : l.debit })}
                    />
                  </td>
                  <td>
                    {lines.length > 2 && (
                      <button
                        type="button"
                        className="secondary"
                        aria-label={`Remove line ${i + 1}`}
                        onClick={() => setLines(lines.filter((_, idx) => idx !== i))}
                      >
                        ×
                      </button>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
            <tfoot>
              <tr>
                <td colSpan={2}>
                  <button type="button" className="secondary" onClick={() => setLines([...lines, blank()])}>
                    Add line
                  </button>
                </td>
                <td style={{ textAlign: "right", fontWeight: 600 }}>{omr(totalDebit)}</td>
                <td style={{ textAlign: "right", fontWeight: 600 }}>{omr(totalCredit)}</td>
                <td></td>
              </tr>
            </tfoot>
          </table>

          <p className={balanced ? "muted" : "error"} style={{ marginTop: 12 }}>
            {totalDebit === 0 && totalCredit === 0
              ? "Enter the lines."
              : balanced
                ? "Balanced."
                : `Out of balance by ${omr(Math.abs(diff))}.`}
          </p>
          {error && <div className="error">{error}</div>}
          <button type="submit" disabled={busy || !balanced}>
            {busy ? "Posting…" : "Post entry"}
          </button>
        </div>
      </form>
    </>
  );
}
