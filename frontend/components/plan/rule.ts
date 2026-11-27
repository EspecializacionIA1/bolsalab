import { planActions, planCopy } from "@/lib/content/plan";
import type { Result } from "@/schemas/prediction";
import type { PlanActionId, SavedRule } from "@/schemas/rule";

const LOW_ASSETS_LEVEL = 2;

export function suggestedActions(result: Result | null, assetsLevel?: number): PlanActionId[] {
  const suggested: PlanActionId[] = [];
  if (result?.category === "more_likely") suggested.push("wait");
  if (assetsLevel !== undefined && assetsLevel <= LOW_ASSETS_LEVEL) suggested.push("needMoney", "cushion");
  if (result?.overconfident) suggested.push("howDoIKnow");
  return suggested;
}

export function defaultRule(result: Result | null, assetsLevel?: number): SavedRule {
  const suggested = suggestedActions(result, assetsLevel);
  return { drop: planCopy.defaultDrop, actions: suggested.length > 0 ? suggested : ["wait"], other: "" };
}

export function ruleSentence(rule: SavedRule): string | null {
  const actions = [
    ...planActions.filter((action) => rule.actions.includes(action.id)).map((action) => action.label),
    ...(rule.other.trim() ? [rule.other.trim()] : []),
  ];
  if (actions.length === 0) return null;
  const joined =
    actions.length === 1 ? actions[0] : `${actions.slice(0, -1).join(", ")} ${planCopy.and} ${actions.at(-1)}`;
  return planCopy.rule(rule.drop, joined);
}
