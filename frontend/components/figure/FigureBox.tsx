import type { ReactNode } from "react";

const gridBackground =
  "bg-[linear-gradient(var(--color-border)_1px,transparent_1px),linear-gradient(90deg,var(--color-border)_1px,transparent_1px)] bg-[size:32px_32px]";

export function FigureBox({ className = "", children }: { className?: string; children: ReactNode }) {
  return (
    <div className={`aspect-square w-full rounded-md border border-border bg-surface ${gridBackground} ${className}`}>
      {children}
    </div>
  );
}
