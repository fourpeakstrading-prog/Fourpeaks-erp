import { useEffect, useState } from "react";
import { NavLink, Outlet } from "react-router-dom";
import { api, type CompanySettings, type Role } from "./api";
import { useAuth } from "./auth";

interface Item {
  to: string;
  label: string;
  roles?: Role[]; // undefined = everyone; owner always passes
  end?: boolean;
}

const NAV: { heading: string; items: Item[] }[] = [
  { heading: "", items: [{ to: "/", label: "Dashboard", end: true }] },
  {
    heading: "Accounting",
    items: [
      { to: "/journal", label: "Journal", roles: ["accountant"] },
      { to: "/accounts", label: "Chart of accounts" },
      { to: "/reports/trial-balance", label: "Trial balance" },
      { to: "/periods", label: "Period close", roles: ["accountant"] },
    ],
  },
  {
    heading: "Admin",
    items: [
      { to: "/users", label: "Users", roles: [] },
      { to: "/settings", label: "Settings", roles: [] },
    ],
  },
];

export default function Shell() {
  const { user, logout } = useAuth();
  const [settings, setSettings] = useState<CompanySettings | null>(null);

  useEffect(() => {
    api.settings.get().then(setSettings).catch(() => setSettings(null));
  }, []);

  const allowed = (item: Item) =>
    !item.roles || user?.role === "owner" || (user ? item.roles.includes(user.role) : false);

  return (
    <div className="shell">
      <aside className="sidebar">
        <div className="company">{settings?.company_name ?? "Four Peaks ERP"}</div>
        <nav>
          {NAV.map((group) => {
            const items = group.items.filter(allowed);
            if (items.length === 0) return null;
            return (
              <div key={group.heading || "top"} style={{ marginBottom: 14 }}>
                {group.heading && <div className="nav-heading">{group.heading}</div>}
                {items.map((it) => (
                  <NavLink key={it.to} to={it.to} end={it.end}>
                    {it.label}
                  </NavLink>
                ))}
              </div>
            );
          })}
        </nav>
        <div className="me">
          {user?.name}
          <br />
          {user?.role}
          <br />
          <a
            href="#"
            onClick={(e) => {
              e.preventDefault();
              logout();
            }}
          >
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
