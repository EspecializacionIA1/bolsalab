import { ruleSentence } from "@/components/plan/rule";
import { Chip } from "@/components/ui/Chip";
import { Eyebrow } from "@/components/ui/Eyebrow";
import { planActions, planCopy } from "@/lib/content/plan";
import type { PlanActionId, SavedRule } from "@/schemas/rule";

const OTHER_MAX_LENGTH = 120;

type RuleBuilderProps = {
  rule: SavedRule;
  suggested: PlanActionId[];
  onChange: (rule: SavedRule) => void;
};

export function RuleBuilder({ rule, suggested, onChange }: RuleBuilderProps) {
  const sentence = ruleSentence(rule);

  function toggle(id: PlanActionId) {
    const actions = rule.actions.includes(id) ? rule.actions.filter((item) => item !== id) : [...rule.actions, id];
    onChange({ ...rule, actions });
  }

  return (
    <div className="flex flex-col gap-6">
      <fieldset className="flex flex-col gap-3">
        <legend className="mb-3 font-medium">{planCopy.dropQuestion}</legend>
        <div className="flex flex-wrap gap-2">
          {planCopy.drops.map((option) => (
            <Chip
              key={option}
              type="radio"
              name="plan-drop"
              checked={rule.drop === option}
              onChange={() => onChange({ ...rule, drop: option })}
            >
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
              checked={rule.actions.includes(action.id)}
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
            value={rule.other}
            maxLength={OTHER_MAX_LENGTH}
            onChange={(event) => onChange({ ...rule, other: event.target.value })}
            className="h-11 rounded-md border border-border bg-surface px-4 text-base text-foreground focus:border-primary"
          />
        </label>
      </fieldset>

      <div aria-live="polite" className="flex flex-col gap-2 rounded-md border border-primary/60 bg-primary/5 p-5">
        <Eyebrow>{planCopy.ruleTitle}</Eyebrow>
        {sentence ? <p className="text-xl leading-snug">{sentence}</p> : <p className="text-muted">{planCopy.empty}</p>}
        <p className="text-sm text-muted">{planCopy.note}</p>
      </div>
    </div>
  );
}
