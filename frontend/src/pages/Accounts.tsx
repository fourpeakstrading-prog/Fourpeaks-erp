import { useCallback, useEffect, useState, type FormEvent } from "react";
import { api, ApiError, type Account, type AccountType } from "../api";
import { useAuth } from "../auth";

const TYPES: AccountType[] = ["asset", "liability", "equity", "income", "expense"];

export default function Accounts() {
  const { user } = useAuth();
  const canEdit = user?.role === "owner" || user?.role === "accountant";
  const [rows, setRows] = useState<Account[]>([]);
  const [showInactive, setShowInactive] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [form, setForm] = useState({ code: "", name: "", type: "expense" as AccountType });

  const load = useCallback(async () => {
    try {
      setRows(await api.accounts.list(showInactive));
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Could not load accounts.");
    }
  }, [showInactive]);

  useEffect(() => {
    void load();
  }, [load]);

  async function onCreate(e: FormEvent) {
    e.preventDefault();
    setError(null);
    if (!/^\d{4}$/.test(form.code) || !form.name.trim()) {
      setError("Code must be four digits and the name cannot be empty.");
      return;
    }
    try {
      await api.accounts.create({ ...form, name: form.name.trim() });
      setForm({ code: "", name: "", type: "expense" });
      await load();
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Could not create account.");
    }
  }

  async function toggle(a: Account) {
    setError(null);
    try {
      await api.accounts.update(a.id, { active: !a.active });
      await load();
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Could not update account.");
    }
  }

  return (
    <>
      <h1>Chart of accounts</h1>
      <p className="muted">
        <label style={{ display: "inline-flex", gap: 6, alignItems: "center" }}>
          <input
            type="checkbox"
            style={{ width: "auto" }}
            checked={showInactive}
            onChange={(e) => setShowInactive(e.target.checked)}
          />
          Show inactive accounts
        </label>
      </p>
      {error && <div className="error">{error}</div>}
      <table>
        <thead>
          <tr>
            <th>Code</th>
            <th>Name</th>
            <th>Type</th>
            <th>Status</th>
            {canEdit && <th></th>}
          </tr>
        </thead>
        <tbody>
          {rows.map((a) => (
            <tr key={a.id}>
              <td>{a.code}</td>
              <td>{a.name}</td>
              <td>{a.type}</td>
              <td>{a.active ? "Active" : "Inactive"}</td>
              {canEdit && (
                <td>
                  {a.system_key ? (
                    <span className="muted">System account</span>
                  ) : (
                    <button className="secondary" onClick={() => toggle(a)}>
                      {a.active ? "Deactivate" : "Reactivate"}
                    </button>
                  )}
                </td>
              )}
            </tr>
          ))}
        </tbody>
      </table>

      {canEdit && (
        <>
          <h2>Add an account</h2>
          <form className="card" onSubmit={onCreate} noValidate>
            <div className="row">
              <div className="field">
                <label htmlFor="code">Code</label>
                <input
                  id="code"
                  value={form.code}
                  maxLength={4}
                  onChange={(e) => setForm({ ...form, code: e.target.value })}
                />
              </div>
              <div className="field">
                <label htmlFor="name">Name</label>
                <input
                  id="name"
                  value={form.name}
                  onChange={(e) => setForm({ ...form, name: e.target.value })}
                />
              </div>
              <div className="field">
                <label htmlFor="type">Type</label>
                <select
                  id="type"
                  value={form.type}
                  onChange={(e) => setForm({ ...form, type: e.target.value as AccountType })}
                >
                  {TYPES.map((t) => (
                    <option key={t} value={t}>
                      {t}
                    </option>
                  ))}
                </select>
              </div>
            </div>
            <button type="submit">Add account</button>
          </form>
        </>
      )}
    </>
  );
}
