import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { listBrokers, updateBrokerStatus } from "../api/admin";
import { useAuth } from "../auth/AuthContext";
import { toDate } from "../components/formatters";
import { StateCard } from "../components/StateCard";

export function AdminBrokersPage(): JSX.Element {
  const { user } = useAuth();
  const queryClient = useQueryClient();
  const brokersQuery = useQuery({
    queryKey: ["adminBrokers"],
    queryFn: listBrokers,
    enabled: user?.role === "manager",
  });
  const statusMutation = useMutation({
    mutationFn: ({ brokerId, isActive }: { brokerId: string; isActive: boolean }) => {
      return updateBrokerStatus(brokerId, isActive);
    },
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["adminBrokers"] }),
  });

  if (user?.role !== "manager") {
    return <p className="text-sm text-red-700">Manager access required.</p>;
  }
  if (brokersQuery.isLoading) {
    return <p className="text-sm text-slate-600">Loading brokers...</p>;
  }
  if (brokersQuery.isError) {
    return <p className="text-sm text-red-700">Failed to load brokers.</p>;
  }

  return (
    <div className="space-y-4">
      <h2 className="text-lg font-semibold">Brokers</h2>
      {(brokersQuery.data ?? []).map((broker) => (
        <StateCard key={broker.id} title={broker.email}>
          <div className="space-y-2 text-sm">
            <p>Registered: {toDate(broker.created_at)}</p>
            <p>Status: {broker.is_active ? "active" : "inactive"}</p>
            <button
              className="rounded-md border border-slate-300 px-3 py-1 hover:bg-slate-100 disabled:opacity-50"
              disabled={statusMutation.isPending}
              onClick={() => statusMutation.mutate({ brokerId: broker.id, isActive: !broker.is_active })}
              type="button"
            >
              {broker.is_active ? "Deactivate" : "Reactivate"}
            </button>
          </div>
        </StateCard>
      ))}
      {brokersQuery.data?.length === 0 ? <p className="text-sm text-slate-600">No brokers found.</p> : null}
    </div>
  );
}
