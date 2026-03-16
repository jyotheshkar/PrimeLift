import Link from "next/link";

type AppHeaderProps = {
  current: "overview" | "uplift" | "recommendations" | "dataset-models";
  sliceLabel: string;
};

const navItems = [
  { key: "overview", label: "Overview", href: "/" },
  { key: "uplift", label: "Uplift Insights", href: "/uplift-insights" },
  { key: "recommendations", label: "Recommendations", href: "/recommendations" },
  { key: "dataset-models", label: "Dataset & Models", href: "/dataset-models" },
] as const;

export function AppHeader({ current, sliceLabel }: AppHeaderProps) {
  return (
    <header className="rounded-[32px] border border-slate-900/10 bg-white/78 px-5 py-4 shadow-[0_22px_80px_rgba(15,23,42,0.08)] backdrop-blur-xl">
      <div className="flex flex-col gap-4 lg:flex-row lg:items-center lg:justify-between">
        <div>
          <p className="text-xs font-semibold uppercase tracking-[0.34em] text-slate-500">
            PrimeLift AI
          </p>
          <p className="mt-2 text-sm text-slate-600">{sliceLabel}</p>
        </div>

        <nav className="flex flex-wrap gap-2">
          {navItems.map((item) => {
            const isActive = item.key === current;
            return (
              <Link
                key={item.key}
                href={item.href}
                className={
                  isActive
                    ? "rounded-full border border-slate-900/10 bg-slate-950 px-4 py-2 text-xs font-semibold uppercase tracking-[0.24em] text-white"
                    : "rounded-full border border-teal-700/15 bg-teal-500/10 px-4 py-2 text-xs font-semibold uppercase tracking-[0.24em] text-teal-900 transition-colors hover:bg-teal-500/15"
                }
              >
                {item.label}
              </Link>
            );
          })}
        </nav>
      </div>
    </header>
  );
}
