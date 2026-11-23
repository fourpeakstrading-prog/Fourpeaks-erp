import { useCallback, useEffect, useState, type FormEvent } from "react";
import { api, ApiError, type Role, type User } from "../api";
import { useAuth } from "../auth";

const ROLES: Role[] = ["owner", "accountant", "sales", "stores", "hr", "viewer"];

export default function Users() {
  const { user: me } = useAuth();
  const [users, setUsers] = useState<User[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [form, setForm] = useState({ name: "", email: "", password: "", role: "viewer" as Role });
  const [busy, setBusy] = useState(false);

  const load = useCallback(async () => {
    try {
      setUsers(await api.users.list());
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Could not load users.");
    }
  }, []);

  useEffect(() => {
    void load();
  }, [load]);

  async function onCreate(e: FormEvent) {
    e.preventDefault();
    setError(null);
    if (!form.name.trim() || !form.email.trim() || form.password.length < 8) {
      setError("Name, email and a password of at least 8 characters are required.");
      return;
    }
    setBusy(true);
    try {
      await api.users.create({ ...form, name: form.name.trim(), email: form.email.trim() });
      setForm({ name: "", email: "", password: "", role: "viewer" });
      await load();
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Could not create user.");
    } finally {
      setBusy(false);
    }
  }

  async function setRole(u: User, role: Role) {
    try {
      await api.users.update(u.id, { role });
      await load();
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Could not update user.");
    }
  }

  async function toggleActive(u: User) {
    try {
      await api.users.update(u.id, { active: !u.active });
      await load();
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Could not update user.");
    }
  }

  return (
    <>
      <h1>Users</h1>
      {error && <div className="error">{error}</div>}
      <table>
        <thead>
          <tr>
            <th>Name</th>
            <th>Email</th>
            <th>Role</th>
            <th>Status</th>
            <th></th>
          </tr>
        </thead>
        <tbody>
          {users.map((u) => (
            <tr key={u.id}>
              <td>{u.name}</td>
              <td>{u.email}</td>
              <td>
                <select
                  value={u.role}
                  disabled={u.id === me?.id}
                  onChange={(e) => setRole(u, e.target.value as Role)}
                >
                  {ROLES.map((r) => (
                    <option key={r} value={r}>
                      {r}
                    </option>
                  ))}
                </select>
              </td>
              <td>{u.active ? "Active" : "Deactivated"}</td>
              <td>
                {u.id !== me?.id && (
                  <button className="secondary" onClick={() => toggleActive(u)}>
                    {u.active ? "Deactivate" : "Reactivate"}
                  </button>
                )}
              </td>
            </tr>
          ))}
        </tbody>
      </table>

      <h2>Add a user</h2>
      <form className="card" onSubmit={onCreate} noValidate>
        <div className="row">
          <div className="field">
            <label htmlFor="n">Name</label>
            <input id="n" value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} />
          </div>
          <div className="field">
            <label htmlFor="e">Email</label>
            <input id="e" type="email" value={form.email} onChange={(e) => setForm({ ...form, email: e.target.value })} />
          </div>
          <div className="field">
            <label htmlFor="p">Password</label>
            <input id="p" type="password" value={form.password} onChange={(e) => setForm({ ...form, password: e.target.value })} />
          </div>
          <div className="field">
            <label htmlFor="r">Role</label>
            <select id="r" value={form.role} onChange={(e) => setForm({ ...form, role: e.target.value as Role })}>
              {ROLES.map((r) => (
                <option key={r} value={r}>
                  {r}
                </option>
              ))}
            </select>
          </div>
        </div>
        <button type="submit" disabled={busy}>
          {busy ? "Adding…" : "Add user"}
        </button>
      </form>
    </>
  );
}
