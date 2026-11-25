import type { ReactNode } from "react";

type SummaryCardProps = {
  id: string;
  title: string;
  className?: string;
  children: ReactNode;
};

export function SummaryCard({ id, title, className = "", children }: SummaryCardProps) {
  return (
    <section
      aria-labelledby={id}
      className={`flex break-inside-avoid flex-col gap-3 rounded-md border border-border bg-surface p-5 print:gap-2 print:p-3 ${className}`}
    >
      <h2 id={id} className="font-mono text-[11px] tracking-[0.08em] text-primary uppercase">
        {title}
      </h2>
      {children}
    </section>
  );
}
