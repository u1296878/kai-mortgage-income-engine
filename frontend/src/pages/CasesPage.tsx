import { useMutation, useQuery } from "@tanstack/react-query";
import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { createCase, listCases } from "../api/cases";
import { StateCard } from "../components/StateCard";
import { toDate } from "../components/formatters";
import { useAuth } from "../auth/AuthContext";

export function CasesPage(): JSX.Element {
  const { user } = useAuth();
  const navigate = useNavigate();
  const [title, setTitle] = useState("");
  const [showForm, setShowForm] = useState(false);
  const casesQuery = useQuery({ queryKey: ["cases"], queryFn: listCases });
  const createMutation = useMutation({
    mutationFn: (newTitle: string) => createCase(newTitle),
    onSuccess: (createdCase) => navigate(`/cases/${createdCase.id}`),
  });

  const createForm = (
    <form
      className="mb-4 flex flex-wrap gap-2"
      onSubmit={(event) => {
        event.preventDefault();
        if (title.trim()) {
          createMutation.mutate(title.trim());
        }
      }}
    >
      <input
        className="min-w-64 rounded-md border border-slate-300 px-3 py-2 text-sm"
        onChange={(event) => setTitle(event.target.value)}
        placeholder="Case title"
        required
        value={title}
      />
      <button className="rounded-md bg-slate-900 px-4 py-2 text-sm text-white" type="submit">
        Create case
      </button>
    </form>
  );

  if (casesQuery.isLoading) {
    return <p className="text-sm text-slate-600">Loading cases...</p>;
  }

  if (casesQuery.isError) {
    return (
      <p className="rounded-md border border-red-200 bg-red-50 p-4 text-sm text-red-700">
        Failed to load cases: {casesQuery.error.message}
      </p>
    );
  }

  if (!casesQuery.data || casesQuery.data.length === 0) {
    return (
      <div>
        <button className="mb-3 rounded-md bg-slate-900 px-4 py-2 text-sm text-white" onClick={() => setShowForm(true)} type="button">
          New Case
        </button>
        {showForm ? createForm : null}
        <p className="text-sm text-slate-600">No cases yet.</p>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      <button className="rounded-md bg-slate-900 px-4 py-2 text-sm text-white" onClick={() => setShowForm((open) => !open)} type="button">
        New Case
      </button>
      {showForm ? createForm : null}
      {casesQuery.data.map((item) => (
        <StateCard key={item.id} title={item.title}>
          <div className="space-y-1 text-sm">
            <p>Case ID: {item.id}</p>
            <p>Status: {item.status}</p>
            <p>Created: {toDate(item.created_at)}</p>
            {user?.role === "manager" ? <p>Broker ID: {item.broker_id}</p> : null}
            <Link className="text-blue-700 underline" to={`/cases/${item.id}`}>
              Open case
            </Link>
          </div>
        </StateCard>
      ))}
    </div>
  );
}
