import { useAuth } from "../auth";

export default function Dashboard() {
  const { user } = useAuth();
  return (
    <>
      <h1>Dashboard</h1>
      <p className="muted">
        Signed in as {user?.name} ({user?.role}). Cash, debtors, creditors and stock tiles arrive
        with the accounting and inventory stages.
      </p>
    </>
  );
}
