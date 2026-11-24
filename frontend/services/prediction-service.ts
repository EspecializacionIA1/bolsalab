import {
  answersSchema,
  healthSchema,
  resultSchema,
  type Answers,
  type Health,
  type Result,
} from "@/schemas/prediction";
import { ApiError, request } from "@/services/api-client";

export function getHealth(): Promise<Health> {
  return request("/health", healthSchema);
}

export async function predict(answers: Partial<Answers>): Promise<Result> {
  const body = answersSchema.safeParse(answers);
  if (!body.success) {
    throw new ApiError("validation", body.error.issues.map((issue) => String(issue.path[0])));
  }

  return request("/v1/crash-reaction/predict", resultSchema, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body.data),
  });
}
