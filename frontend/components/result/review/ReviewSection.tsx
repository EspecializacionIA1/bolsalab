"use client";

import { useState } from "react";
import { QuizCard, type QuizAnswer } from "@/components/result/review/QuizCard";
import { WhatIf } from "@/components/result/review/WhatIf";
import { Button } from "@/components/ui/Button";
import { Eyebrow } from "@/components/ui/Eyebrow";
import { Notice } from "@/components/ui/Notice";
import { knowledgeFields, reviewCopy, reviewQuestions } from "@/lib/content/quiz";
import type { Answers, Result } from "@/schemas/prediction";

type ReviewSectionProps = {
  result: Result;
  answers: Partial<Answers>;
};

export function ReviewSection({ result, answers }: ReviewSectionProps) {
  const [started, setStarted] = useState(false);
  const [index, setIndex] = useState(0);
  const [responses, setResponses] = useState<QuizAnswer[]>([]);

  const failed = knowledgeFields.filter((field) => result.failed_questions.includes(field));
  if (failed.length === 0) return null;

  const askCertainty = result.overconfident;
  const total = failed.length;
  const finished = index === total;
  const field = failed[index];

  const correct = responses.filter((response) => response.correct).length;
  const sure = responses.filter((response) => response.certainty === "sure").length;
  const sureAndWrong = responses.some((response) => response.certainty === "sure" && !response.correct);

  return (
    <section aria-labelledby="review-title" className="flex flex-col gap-6 border-t border-border pt-10">
      <div className="flex flex-col gap-2">
        {started && !finished && <Eyebrow>{reviewCopy.progress(index + 1, total)}</Eyebrow>}
        <h2 id="review-title" className="text-2xl font-medium tracking-[-0.01em] md:text-3xl">
          {reviewCopy.title}
        </h2>
      </div>

      {!started && (
        <div className="flex flex-col items-start gap-4">
          <p className="text-muted">{reviewCopy.intro(total)}</p>
          <Button variant="ghost" onClick={() => setStarted(true)}>
            {reviewCopy.start}
          </Button>
        </div>
      )}

      {started && !finished && (
        <QuizCard
          key={field}
          name={`review-${field}`}
          question={reviewQuestions[field]}
          askCertainty={askCertainty}
          isLast={index === total - 1}
          onAnswered={(response) => setResponses((previous) => [...previous, response])}
          onNext={() => setIndex(index + 1)}
          afterReveal={<WhatIf field={field} answers={answers} current={result.category} />}
        />
      )}

      {finished && (
        <Notice title={reviewCopy.summaryTitle}>
          <p>
            {askCertainty ? reviewCopy.summaryWithCertainty(sure, correct, total) : reviewCopy.summary(correct, total)}
          </p>
          {sureAndWrong && <p className="mt-2">{reviewCopy.summarySureAndWrong}</p>}
        </Notice>
      )}
    </section>
  );
}
