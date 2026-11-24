import { z } from "zod";

const level = z.int().min(1).max(5);

export const answersSchema = z.object({
  age: z.int().min(18).max(100),
  male: z.boolean(),
  university: z.boolean(),
  married: z.boolean(),
  has_children: z.boolean(),
  urban: z.boolean(),
  employed: z.boolean(),
  income_level: level,
  assets_level: level,
  knowledge_confidence: level,
  interest: z.enum(["more", "exactly", "less", "dont_know"]),
  inflation: z.enum(["more", "same", "less", "dont_know"]),
  diversification: z.enum(["true", "false", "dont_know"]),
});

const factorSchema = z.object({
  feature: z.string(),
  label: z.string(),
  direction: z.enum(["increases", "decreases"]),
  impact: z.number(),
  actionable: z.boolean(),
});

export const resultSchema = z.object({
  model_version: z.string(),
  category: z.enum(["less_likely", "similar", "more_likely"]),
  top_factors: z.array(factorSchema),
  failed_questions: z.array(z.enum(["interest", "inflation", "diversification"])),
  overconfident: z.boolean(),
  not_asked: z.array(z.string()),
  warnings: z.array(z.string()),
});

export const healthSchema = z.object({
  status: z.literal("ok"),
  model_version: z.string(),
});

export const validationErrorSchema = z.object({
  detail: z.array(z.object({ loc: z.array(z.union([z.string(), z.number()])) })),
});

export type Answers = z.infer<typeof answersSchema>;
export type Factor = z.infer<typeof factorSchema>;
export type Result = z.infer<typeof resultSchema>;
export type Health = z.infer<typeof healthSchema>;
