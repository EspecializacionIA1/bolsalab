import type { z } from "zod";
import { validationErrorSchema } from "@/schemas/prediction";

const API_URL = "/api";
const TIMEOUT_MS = 15_000;

export type ApiErrorKind = "validation" | "rate_limit" | "network" | "server" | "invalid_response";

export class ApiError extends Error {
  kind: ApiErrorKind;
  fields: string[];

  constructor(kind: ApiErrorKind, fields: string[] = []) {
    super(kind);
    this.name = "ApiError";
    this.kind = kind;
    this.fields = fields;
  }
}

async function send(path: string, init?: RequestInit): Promise<Response> {
  try {
    return await fetch(`${API_URL}${path}`, { ...init, signal: AbortSignal.timeout(TIMEOUT_MS) });
  } catch {
    throw new ApiError("network");
  }
}

async function readInvalidFields(response: Response): Promise<string[]> {
  const body = validationErrorSchema.safeParse(await response.json().catch(() => null));
  if (!body.success) return [];
  return body.data.detail.map((issue) => String(issue.loc.at(-1)));
}

export async function request<T>(path: string, schema: z.ZodType<T>, init?: RequestInit): Promise<T> {
  const response = await send(path, init);

  if (response.status === 422) throw new ApiError("validation", await readInvalidFields(response));
  if (response.status === 429) throw new ApiError("rate_limit");
  if (!response.ok) throw new ApiError("server");

  const body = schema.safeParse(await response.json().catch(() => null));
  if (!body.success) throw new ApiError("invalid_response");
  return body.data;
}
