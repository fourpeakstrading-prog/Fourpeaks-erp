import { BrowserRouter, Navigate, Outlet, Route, Routes } from "react-router-dom";
import { AuthProvider, useAuth } from "./auth";
import type { Role } from "./api";
import Shell from "./Shell";
import Accounts from "./pages/Accounts";
import Dashboard from "./pages/Dashboard";
import Journal from "./pages/Journal";
import Login from "./pages/Login";
import NewEntry from "./pages/NewEntry";
import Periods from "./pages/Periods";
import Settings from "./pages/Settings";
import TrialBalance from "./pages/TrialBalance";
import Users from "./pages/Users";

function RequireAuth() {
  const { user, loading } = useAuth();
  if (loading) return <p className="muted" style={{ padding: 24 }}>Loading…</p>;
  return user ? <Outlet /> : <Navigate to="/login" replace />;
}

function RequireRole({ roles }: { roles: Role[] }) {
  const { user } = useAuth();
  return user && (user.role === "owner" || roles.includes(user.role)) ? (
    <Outlet />
  ) : (
    <Navigate to="/" replace />
  );
}

export default function App() {
  return (
    <AuthProvider>
      <BrowserRouter>
        <Routes>
          <Route path="/login" element={<Login />} />
          <Route element={<RequireAuth />}>
            <Route element={<Shell />}>
              <Route index element={<Dashboard />} />
              <Route path="accounts" element={<Accounts />} />
              <Route path="reports/trial-balance" element={<TrialBalance />} />
              <Route element={<RequireRole roles={["accountant"]} />}>
                <Route path="journal" element={<Journal />} />
                <Route path="journal/new" element={<NewEntry />} />
                <Route path="periods" element={<Periods />} />
              </Route>
              <Route element={<RequireRole roles={[]} />}>
                <Route path="users" element={<Users />} />
                <Route path="settings" element={<Settings />} />
              </Route>
            </Route>
          </Route>
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </BrowserRouter>
    </AuthProvider>
  );
}
