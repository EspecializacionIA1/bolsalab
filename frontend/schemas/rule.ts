import { z } from "zod";

export const planActionIds = ["wait", "needMoney", "reason", "cushion", "news", "howDoIKnow", "talk"] as const;

export const ruleSchema = z.object({
  drop: z.string(),
  actions: z.array(z.enum(planActionIds)),
  other: z.string().max(120),
});

export type PlanActionId = (typeof planActionIds)[number];
export type SavedRule = z.infer<typeof ruleSchema>;
