import type { PropsWithChildren } from "react";

interface StateCardProps extends PropsWithChildren {
  title: string;
}

export function StateCard({ title, children }: StateCardProps): JSX.Element {
  return (
    <section className="rounded-lg border border-slate-200 bg-white p-4 shadow-sm">
      <h2 className="mb-3 text-sm font-semibold uppercase tracking-wide text-slate-600">{title}</h2>
      {children}
    </section>
  );
}
