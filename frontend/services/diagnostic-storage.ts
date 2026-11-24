import { z } from "zod";
import { answersSchema, resultSchema } from "@/schemas/prediction";

const STORAGE_KEY = "bolsalab.diagnostic";

const savedDiagnosticSchema = z.object({
  answers: answersSchema.partial(),
  result: resultSchema.nullable(),
});

export type SavedDiagnostic = z.infer<typeof savedDiagnosticSchema>;

export const emptyDiagnostic: SavedDiagnostic = { answers: {}, result: null };

export function loadDiagnostic(): SavedDiagnostic {
  try {
    const stored = JSON.parse(sessionStorage.getItem(STORAGE_KEY) ?? "null");
    const saved = savedDiagnosticSchema.safeParse(stored);
    return saved.success ? saved.data : emptyDiagnostic;
  } catch {
    return emptyDiagnostic;
  }
}

export function saveDiagnostic(diagnostic: SavedDiagnostic): void {
  try {
    sessionStorage.setItem(STORAGE_KEY, JSON.stringify(diagnostic));
  } catch {
    return;
  }
}
