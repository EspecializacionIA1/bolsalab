import { factorsCopy } from "@/lib/content/result";
import type { Factor } from "@/schemas/prediction";

const MIN_BAR_PERCENT = 8;

const directionColors: Record<Factor["direction"], { text: string; bar: string }> = {
  increases: { text: "text-sells", bar: "bg-sells" },
  decreases: { text: "text-holds", bar: "bg-holds" },
};

type FactorListProps = {
  factors: Factor[];
  maxImpact: number;
};

export function FactorList({ factors, maxImpact }: FactorListProps) {
  return (
    <ul className="flex flex-col gap-4">
      {factors.map((factor) => {
        const colors = directionColors[factor.direction];
        const width = Math.max(MIN_BAR_PERCENT, (factor.impact / maxImpact) * 100);
        return (
          <li key={factor.feature} className="flex flex-col gap-2">
            <div className="flex flex-wrap items-baseline justify-between gap-x-4 gap-y-1">
              <span>{factor.label}</span>
              <span className={`font-mono text-xs ${colors.text}`}>{factorsCopy.directions[factor.direction]}</span>
            </div>
            <span aria-hidden className="print-track h-1.5 rounded-[1px] bg-surface-raised">
              <span className={`print-bar block h-full rounded-[1px] ${colors.bar}`} style={{ width: `${width}%` }} />
            </span>
          </li>
        );
      })}
    </ul>
  );
}
