type MetricCardProps = {
  label: string;
  value: string;
  detail: string;
  accent: "teal" | "amber" | "slate" | "coral";
};

const accentMap: Record<MetricCardProps["accent"], string> = {
  teal: "from-teal-300/70 via-teal-200/40 to-transparent",
  amber: "from-amber-300/80 via-orange-200/40 to-transparent",
  slate: "from-slate-400/40 via-slate-300/20 to-transparent",
  coral: "from-rose-300/70 via-orange-200/40 to-transparent",
};

export function MetricCard({ label, value, detail, accent }: MetricCardProps) {
  return (
    <article className="group relative overflow-hidden rounded-[28px] border border-slate-900/10 bg-white/85 p-5 shadow-[0_20px_60px_rgba(15,23,42,0.08)] backdrop-blur-xl">
      <div
        className={`pointer-events-none absolute inset-x-0 top-0 h-24 bg-gradient-to-br ${accentMap[accent]} opacity-90 transition-opacity group-hover:opacity-100`}
      />
      <div className="relative">
        <p className="text-xs font-medium uppercase tracking-[0.24em] text-slate-500">
          {label}
        </p>
        <p className="mt-5 text-3xl font-semibold tracking-tight text-slate-950">
          {value}
        </p>
        <p className="mt-3 max-w-xs text-sm leading-6 text-slate-600">{detail}</p>
      </div>
    </article>
  );
}
