"use client";

import { useState } from "react";
import { Button } from "@/components/ui/Button";
import { Chip } from "@/components/ui/Chip";
import { Eyebrow } from "@/components/ui/Eyebrow";
import { planActions, planCopy, type PlanActionId } from "@/lib/content/plan";
import type { Result } from "@/schemas/prediction";

const LOW_ASSETS_LEVEL = 2;
const OTHER_MAX_LENGTH = 120;

type RuleBuilderProps = {
  result: Result | null;
  assetsLevel?: number;
};

function suggestedActions(result: Result | null, assetsLevel?: number): PlanActionId[] {
  const suggested: PlanActionId[] = [];
  if (result?.category === "more_likely") suggested.push("wait");
  if (assetsLevel !== undefined && assetsLevel <= LOW_ASSETS_LEVEL) suggested.push("needMoney", "cushion");
  if (result?.overconfident) suggested.push("howDoIKnow");
  return suggested;
}

function joinActions(items: string[]) {
  if (items.length <= 1) return items.join("");
  return `${items.slice(0, -1).join(", ")} ${planCopy.and} ${items.at(-1)}`;
}

export function RuleBuilder({ result, assetsLevel }: RuleBuilderProps) {
  const suggested = suggestedActions(result, assetsLevel);
  const [drop, setDrop] = useState(planCopy.drops[1]);
  const [selected, setSelected] = useState<PlanActionId[]>(() => (suggested.length > 0 ? suggested : ["wait"]));
  const [other, setOther] = useState("");

  const actions = [
    ...planActions.filter((action) => selected.includes(action.id)).map((action) => action.label),
    ...(other.trim() ? [other.trim()] : []),
  ];

  function toggle(id: PlanActionId) {
    setSelected((current) => (current.includes(id) ? current.filter((item) => item !== id) : [...current, id]));
  }

  return (
    <div className="flex flex-col gap-6">
      <fieldset className="flex flex-col gap-3">
        <legend className="mb-3 font-medium">{planCopy.dropQuestion}</legend>
        <div className="flex flex-wrap gap-2">
          {planCopy.drops.map((option) => (
            <Chip key={option} type="radio" name="plan-drop" checked={drop === option} onChange={() => setDrop(option)}>
              {option}
            </Chip>
          ))}
        </div>
      </fieldset>

      <fieldset className="flex flex-col gap-3">
        <legend className="mb-1 font-medium">{planCopy.actionsQuestion}</legend>
        <p className="text-sm text-muted">{planCopy.prefilled}</p>
        <div className="flex flex-wrap gap-2">
          {planActions.map((action) => (
            <Chip
              key={action.id}
              type="checkbox"
              name="plan-actions"
              checked={selected.includes(action.id)}
              onChange={() => toggle(action.id)}
            >
              <span>{action.label}</span>
              {suggested.includes(action.id) && (
                <span className="rounded-sm bg-surface-raised px-1.5 py-0.5 font-mono text-[10px] tracking-[0.06em] text-primary uppercase">
                  {planCopy.suggested}
                </span>
              )}
            </Chip>
          ))}
        </div>
        <label className="mt-2 flex flex-col gap-2 text-sm text-muted">
          {planCopy.otherLabel}
          <input
            value={other}
            maxLength={OTHER_MAX_LENGTH}
            onChange={(event) => setOther(event.target.value)}
            className="h-11 rounded-md border border-border bg-surface px-4 text-base text-foreground focus:border-primary"
          />
        </label>
      </fieldset>

      <div id="rule-card" aria-live="polite" className="flex flex-col gap-2 rounded-md border border-primary/60 bg-primary/5 p-5">
        <Eyebrow>{planCopy.ruleTitle}</Eyebrow>
        {actions.length > 0 ? (
          <p className="text-xl leading-snug">{planCopy.rule(drop, joinActions(actions))}</p>
        ) : (
          <p className="text-muted">{planCopy.empty}</p>
        )}
        <p className="text-sm text-muted">{planCopy.note}</p>
      </div>

      <div className="flex flex-col items-start gap-2">
        <Button disabled={actions.length === 0} onClick={() => window.print()}>
          {planCopy.print}
        </Button>
        <p className="text-sm text-muted">{planCopy.privacy}</p>
      </div>
    </div>
  );
}
