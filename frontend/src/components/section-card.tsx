import type { ReactNode } from "react";

type SectionCardProps = {
  eyebrow: string;
  title: string;
  children: ReactNode;
  className?: string;
};

export function SectionCard({
  eyebrow,
  title,
  children,
  className = "",
}: SectionCardProps) {
  return (
    <section
      className={`rounded-[32px] border border-slate-900/10 bg-white/82 p-6 shadow-[0_24px_80px_rgba(15,23,42,0.08)] backdrop-blur-xl ${className}`.trim()}
    >
      <p className="text-[11px] font-semibold uppercase tracking-[0.28em] text-slate-500">
        {eyebrow}
      </p>
      <h2 className="mt-3 text-2xl font-semibold tracking-tight text-slate-950">
        {title}
      </h2>
      <div className="mt-6">{children}</div>
    </section>
  );
}
