"use client";

import { useState } from "react";
import { Button } from "@/components/ui/Button";
import { submitErrors } from "@/lib/content/diagnostic";
import { originalQuestions, whatIfCopy, type KnowledgeField } from "@/lib/content/quiz";
import type { Answers, Result } from "@/schemas/prediction";
import { ApiError, type ApiErrorKind } from "@/services/api-client";
import { predict } from "@/services/prediction-service";

const rank: Record<Result["category"], number> = { less_likely: 0, similar: 1, more_likely: 2 };

type WhatIfProps = {
  field: KnowledgeField;
  answers: Partial<Answers>;
  current: Result["category"];
};

export function WhatIf({ field, answers, current }: WhatIfProps) {
  const [loading, setLoading] = useState(false);
  const [next, setNext] = useState<Result["category"] | null>(null);
  const [error, setError] = useState<ApiErrorKind | null>(null);

  async function check() {
    setLoading(true);
    setError(null);
    try {
      const result = await predict({ ...answers, [field]: originalQuestions[field].correct });
      setNext(result.category);
    } catch (caught) {
      setError(caught instanceof ApiError ? caught.kind : "server");
    } finally {
      setLoading(false);
    }
  }

  function message(category: Result["category"]) {
    const from = whatIfCopy.tercileNames[current];
    const to = whatIfCopy.tercileNames[category];
    if (category === current) return whatIfCopy.same;
    return rank[category] < rank[current] ? whatIfCopy.better(from, to) : whatIfCopy.worse(from, to);
  }

  return (
    <div className="flex flex-col gap-3 rounded-md border border-dashed border-border p-4">
      <p className="font-medium">{whatIfCopy.title}</p>
      <p className="text-sm text-muted">{whatIfCopy.body}</p>
      <div aria-live="polite">
        {next ? (
          <p>{message(next)}</p>
        ) : (
          <div className="flex flex-col items-start gap-2">
            <Button variant="ghost" onClick={check} disabled={loading}>
              {loading ? whatIfCopy.loading : whatIfCopy.action}
            </Button>
            {error && <p className="text-sm text-sells">{submitErrors[error].title}</p>}
          </div>
        )}
      </div>
    </div>
  );
}
