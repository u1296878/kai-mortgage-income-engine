import { useQuery } from "@tanstack/react-query";
import { Link } from "react-router-dom";
import { listCases } from "../api/cases";
import { StateCard } from "../components/StateCard";
import { toDate } from "../components/formatters";
import { useAuth } from "../auth/AuthContext";

export function CasesPage(): JSX.Element {
  const { user } = useAuth();
  const casesQuery = useQuery({ queryKey: ["cases"], queryFn: listCases });

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
    return <p className="text-sm text-slate-600">No cases yet. Upload a document to get started.</p>;
  }

  return (
    <div className="space-y-4">
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
