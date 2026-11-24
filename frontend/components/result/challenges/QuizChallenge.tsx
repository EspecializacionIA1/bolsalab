"use client";

import { useState } from "react";
import { QuizCard, type QuizAnswer } from "@/components/result/challenges/QuizCard";
import { WhatIf } from "@/components/result/challenges/WhatIf";
import { Button } from "@/components/ui/Button";
import { Eyebrow } from "@/components/ui/Eyebrow";
import { Notice } from "@/components/ui/Notice";
import { knowledgeFields, originalQuestions, quizCopy, variantQuestions } from "@/lib/content/quiz";
import type { Answers, Result } from "@/schemas/prediction";

type QuizChallengeProps = {
  result: Result;
  answers: Partial<Answers>;
};

export function QuizChallenge({ result, answers }: QuizChallengeProps) {
  const [started, setStarted] = useState(false);
  const [index, setIndex] = useState(0);
  const [responses, setResponses] = useState<QuizAnswer[]>([]);

  const steps = knowledgeFields.map((field) => {
    const failed = result.failed_questions.includes(field);
    return { field, failed, question: failed ? originalQuestions[field] : variantQuestions[field] };
  });
  const finished = index === steps.length;
  const step = steps[index];

  const sure = responses.filter((response) => response.certainty === "sure").length;
  const correct = responses.filter((response) => response.correct).length;
  const sureAndWrong = responses.some((response) => response.certainty === "sure" && !response.correct);

  return (
    <section aria-labelledby="quiz-title" className="flex flex-col gap-6 border-t border-border pt-10">
      <div className="flex flex-col gap-2">
        <Eyebrow>{started && !finished ? `${quizCopy.label} · ${quizCopy.progress(index + 1, steps.length)}` : quizCopy.label}</Eyebrow>
        <h2 id="quiz-title" className="text-2xl font-medium tracking-[-0.01em] md:text-3xl">
          {quizCopy.title}
        </h2>
      </div>

      {!started && (
        <div className="flex flex-col items-start gap-4">
          <p className="text-muted">{quizCopy.intro}</p>
          <Button onClick={() => setStarted(true)}>{quizCopy.start} →</Button>
        </div>
      )}

      {started && !finished && (
        <QuizCard
          key={step.field}
          name={`quiz-${step.field}`}
          question={step.question}
          isLast={index === steps.length - 1}
          onAnswered={(response) => setResponses((previous) => [...previous, response])}
          onNext={() => setIndex(index + 1)}
          afterReveal={step.failed && <WhatIf field={step.field} answers={answers} current={result.category} />}
        />
      )}

      {finished && (
        <Notice title={quizCopy.summaryTitle}>
          <p>{quizCopy.summary(sure, correct, steps.length)}</p>
          {sureAndWrong && <p className="mt-2">{quizCopy.summarySureAndWrong}</p>}
        </Notice>
      )}
    </section>
  );
}
