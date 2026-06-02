import { useState } from "react";
import type { FormEvent } from "react";
import { Link, Navigate, useNavigate } from "react-router-dom";
import { register } from "../api/auth";
import { useAuth } from "../auth/AuthContext";

export function RegisterPage(): JSX.Element {
  const { user, loading } = useAuth();
  const navigate = useNavigate();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  if (!loading && user) {
    return <Navigate to="/cases" replace />;
  }

  const submit = async (event: FormEvent<HTMLFormElement>): Promise<void> => {
    event.preventDefault();
    setError(null);
    if (password !== confirmPassword) {
      setError("Passwords do not match");
      return;
    }
    setSubmitting(true);
    try {
      await register({ email, password });
      navigate("/login", { replace: true, state: { registered: true } });
    } catch (caught) {
      const message = caught instanceof Error ? caught.message : "Registration failed";
      setError(message);
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="flex min-h-screen items-center justify-center px-4">
      <form className="w-full max-w-sm space-y-4 rounded-lg border border-slate-200 bg-white p-6 shadow-sm" onSubmit={submit}>
        <h1 className="text-xl font-semibold">Create broker account</h1>
        <p className="text-sm text-slate-600">New accounts are registered as brokers.</p>
        <div>
          <label className="mb-1 block text-sm font-medium" htmlFor="email">Email</label>
          <input
            className="w-full rounded-md border border-slate-300 px-3 py-2 text-sm"
            id="email"
            onChange={(event) => setEmail(event.target.value)}
            required
            type="email"
            value={email}
          />
        </div>
        <div>
          <label className="mb-1 block text-sm font-medium" htmlFor="password">Password</label>
          <input
            className="w-full rounded-md border border-slate-300 px-3 py-2 text-sm"
            id="password"
            onChange={(event) => setPassword(event.target.value)}
            required
            type="password"
            value={password}
          />
        </div>
        <div>
          <label className="mb-1 block text-sm font-medium" htmlFor="confirm-password">Confirm password</label>
          <input
            className="w-full rounded-md border border-slate-300 px-3 py-2 text-sm"
            id="confirm-password"
            onChange={(event) => setConfirmPassword(event.target.value)}
            required
            type="password"
            value={confirmPassword}
          />
        </div>
        {error ? <p className="text-sm text-red-700">{error}</p> : null}
        <button className="w-full rounded-md bg-slate-900 px-4 py-2 text-sm font-medium text-white disabled:opacity-50" disabled={submitting} type="submit">
          {submitting ? "Creating account..." : "Create account"}
        </button>
        <Link className="block text-center text-sm text-blue-700 underline" to="/login">
          Back to sign in
        </Link>
      </form>
    </div>
  );
}
