import { useCallback, useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { api, ApiError, type Account, type JournalEntry } from "../api";
import { omr, today } from "../money";

export default function Journal() {
  const [entries, setEntries] = useState<JournalEntry[]>([]);
  const [accounts, setAccounts] = useState<Record<string, Account>>({});
  const [error, setError] = useState<string | null>(null);
  const [open, setOpen] = useState<string | null>(null);
  const [reverseOn, setReverseOn] = useState(today);

  const load = useCallback(async () => {
    try {
      const [es, as] = await Promise.all([api.journal.list(), api.accounts.list(true)]);
      setEntries(es);
      setAccounts(Object.fromEntries(as.map((a) => [a.id, a])));
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Could not load the journal.");
    }
  }, []);

  useEffect(() => {
    void load();
  }, [load]);

  async function reverse(e: JournalEntry) {
    setError(null);
    try {
      await api.journal.reverse(e.id, reverseOn);
      await load();
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Could not reverse.");
    }
  }

  return (
    <>
      <h1>Journal</h1>
      <p>
        <Link to="/journal/new">
          <button>New manual entry</button>
        </Link>
      </p>
      {error && <div className="error">{error}</div>}
      <table>
        <thead>
          <tr>
            <th>No.</th>
            <th>Date</th>
            <th>Source</th>
            <th>Narration</th>
            <th style={{ textAlign: "right" }}>Amount</th>
            <th></th>
          </tr>
        </thead>
        <tbody>
          {entries.map((e) => {
            const total = e.lines.reduce((s, l) => s + Number(l.debit), 0);
            const isOpen = open === e.id;
            return (
              <EntryRows
                key={e.id}
                e={e}
                total={total}
                isOpen={isOpen}
                accounts={accounts}
                onToggle={() => setOpen(isOpen ? null : e.id)}
                onReverse={() => reverse(e)}
                reverseOn={reverseOn}
                setReverseOn={setReverseOn}
              />
            );
          })}
          {entries.length === 0 && (
            <tr>
              <td colSpan={6} className="muted">
                No entries yet.
              </td>
            </tr>
          )}
        </tbody>
      </table>
    </>
  );
}

function EntryRows(props: {
  e: JournalEntry;
  total: number;
  isOpen: boolean;
  accounts: Record<string, Account>;
  onToggle: () => void;
  onReverse: () => void;
  reverseOn: string;
  setReverseOn: (v: string) => void;
}) {
  const { e, total, isOpen, accounts } = props;
  return (
    <>
      <tr style={{ cursor: "pointer" }} onClick={props.onToggle}>
        <td>{e.number}</td>
        <td>{e.entry_date}</td>
        <td>
          {e.source}
          {e.locked ? " (locked)" : ""}
          {e.reversed_by_id ? " (reversed)" : ""}
        </td>
        <td>{e.narration}</td>
        <td style={{ textAlign: "right" }}>{omr(total)}</td>
        <td className="muted">{isOpen ? "Hide" : "Lines"}</td>
      </tr>
      {isOpen && (
        <tr>
          <td colSpan={6} style={{ background: "var(--bg)" }}>
            <table style={{ border: 0 }}>
              <thead>
                <tr>
                  <th>Account</th>
                  <th>Description</th>
                  <th style={{ textAlign: "right" }}>Debit</th>
                  <th style={{ textAlign: "right" }}>Credit</th>
                </tr>
              </thead>
              <tbody>
                {e.lines.map((l) => (
                  <tr key={l.id}>
                    <td>
                      {accounts[l.account_id]?.code} {accounts[l.account_id]?.name}
                    </td>
                    <td>{l.description}</td>
                    <td style={{ textAlign: "right" }}>{omr(l.debit, true)}</td>
                    <td style={{ textAlign: "right" }}>{omr(l.credit, true)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
            {!e.reversed_by_id && (
              <div style={{ display: "flex", gap: 10, alignItems: "center", marginTop: 10 }}>
                <span className="muted">Reverse on</span>
                <input
                  type="date"
                  style={{ width: "auto" }}
                  value={props.reverseOn}
                  onChange={(ev) => props.setReverseOn(ev.target.value)}
                />
                <button className="secondary" onClick={props.onReverse}>
                  Reverse this entry
                </button>
              </div>
            )}
          </td>
        </tr>
      )}
    </>
  );
}
