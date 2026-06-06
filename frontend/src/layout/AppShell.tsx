import { Link, Outlet } from "react-router-dom";
import { useAuth } from "../auth/AuthContext";

export function AppShell(): JSX.Element {
  const { user, logout } = useAuth();

  return (
    <div className="min-h-screen">
      <header className="border-b border-slate-200 bg-white">
        <div className="mx-auto flex max-w-6xl items-center justify-between px-4 py-3">
          <div className="flex items-center gap-3">
            <h1 className="text-base font-semibold text-slate-900">Kai Mortgage Income Engine</h1>
            <Link className="text-sm text-blue-700 hover:underline" to="/cases">
              Cases
            </Link>
            <Link className="text-sm text-blue-700 hover:underline" to="/income/employment">
              Employment income
            </Link>
            <Link className="text-sm text-blue-700 hover:underline" to="/income/rental">
              Rental income
            </Link>
            {user?.role === "manager" ? (
              <Link className="text-sm text-blue-700 hover:underline" to="/admin/brokers">
                Brokers
              </Link>
            ) : null}
          </div>
          <div className="flex items-center gap-3 text-sm">
            <span>{user?.email}</span>
            <span className="rounded-md border border-slate-300 px-2 py-1">{user?.role}</span>
            <button
              className="rounded-md border border-slate-300 px-3 py-1 hover:bg-slate-100"
              onClick={logout}
              type="button"
            >
              Logout
            </button>
          </div>
        </div>
      </header>
      <main className="mx-auto max-w-6xl px-4 py-6">
        <Outlet />
      </main>
    </div>
  );
}
