import { useEffect, useState } from "react";
import { NavLink, Outlet } from "react-router-dom";
import { api, type CompanySettings } from "./api";
import { useAuth } from "./auth";

export default function Shell() {
  const { user, logout } = useAuth();
  const [settings, setSettings] = useState<CompanySettings | null>(null);

  useEffect(() => {
    api.settings.get().then(setSettings).catch(() => setSettings(null));
  }, []);

  return (
    <div className="shell">
      <aside className="sidebar">
        <div className="company">{settings?.company_name ?? "Four Peaks ERP"}</div>
        <nav>
          <NavLink to="/" end>
            Dashboard
          </NavLink>
          {user?.role === "owner" && <NavLink to="/users">Users</NavLink>}
          {user?.role === "owner" && <NavLink to="/settings">Settings</NavLink>}
        </nav>
        <div className="me">
          {user?.name}
          <br />
          {user?.role}
          <br />
          <a href="#" onClick={(e) => { e.preventDefault(); logout(); }}>
            Sign out
          </a>
        </div>
      </aside>
      <main className="main">
        <Outlet />
      </main>
    </div>
  );
}
