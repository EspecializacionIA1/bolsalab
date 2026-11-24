import { FactorList } from "@/components/result/FactorList";
import { factorsCopy } from "@/lib/content/result";
import type { Factor } from "@/schemas/prediction";

export function FactorsSection({ factors }: { factors: Factor[] }) {
  const maxImpact = Math.max(...factors.map((factor) => factor.impact));
  const actionable = factors.filter((factor) => factor.actionable);
  const situation = factors.filter((factor) => !factor.actionable);

  return (
    <section aria-labelledby="factors-title" className="flex flex-col gap-6 border-t border-border pt-10">
      <div className="flex flex-col gap-3">
        <h2 id="factors-title" className="text-2xl font-medium tracking-[-0.01em] md:text-3xl">
          {factorsCopy.title}
        </h2>
        <p className="flex flex-wrap gap-x-5 gap-y-1 font-mono text-xs">
          <span className="text-sells">■ {factorsCopy.directions.increases}</span>
          <span className="text-holds">■ {factorsCopy.directions.decreases}</span>
        </p>
      </div>

      {actionable.length > 0 && (
        <div className="flex flex-col gap-4">
          <div>
            <h3 className="font-medium">{factorsCopy.actionable.title}</h3>
            <p className="text-sm text-muted">{factorsCopy.actionable.body}</p>
          </div>
          <FactorList factors={actionable} maxImpact={maxImpact} />
        </div>
      )}

      {situation.length > 0 && (
        <details open={actionable.length === 0} className="rounded-md border border-border bg-surface p-5">
          <summary className="cursor-pointer font-medium">
            {factorsCopy.situation.title} ({situation.length})
          </summary>
          <div className="mt-4 flex flex-col gap-4">
            <p className="text-sm text-muted">{factorsCopy.situation.body}</p>
            <FactorList factors={situation} maxImpact={maxImpact} />
          </div>
        </details>
      )}

      <p className="text-sm text-muted">{factorsCopy.note}</p>
    </section>
  );
}
