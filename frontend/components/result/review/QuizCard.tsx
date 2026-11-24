"use client";

import { useState, type ReactNode } from "react";
import { Button } from "@/components/ui/Button";
import { Option } from "@/components/ui/Option";
import { isDontKnow, reviewCopy, type Certainty, type QuizQuestion } from "@/lib/content/quiz";

const letters = "ABCD";
const certainties: Certainty[] = ["guess", "think", "sure"];

export type QuizAnswer = { correct: boolean; certainty: Certainty | null };

type QuizCardProps = {
  name: string;
  question: QuizQuestion;
  askCertainty: boolean;
  isLast: boolean;
  onAnswered: (answer: QuizAnswer) => void;
  onNext: () => void;
  afterReveal?: ReactNode;
};

export function QuizCard({ name, question, askCertainty, isLast, onAnswered, onNext, afterReveal }: QuizCardProps) {
  const [choice, setChoice] = useState<string | null>(null);
  const [answer, setAnswer] = useState<QuizAnswer | null>(null);

  function reveal(value: string, certainty: Certainty | null) {
    const result = { correct: value === question.correct, certainty };
    setAnswer(result);
    onAnswered(result);
  }

  function select(value: string) {
    if (answer) return;
    setChoice(value);
    if (!askCertainty) reveal(value, null);
  }

  function feedback() {
    if (!choice || !answer) return "";
    if (answer.correct) return reviewCopy.correct(question.answerLabel);
    if (isDontKnow(choice)) return reviewCopy.dontKnow(question.answerLabel);
    return reviewCopy.wrong(question.answerLabel);
  }

  return (
    <div className="flex flex-col gap-5">
      <h3 id={`${name}-title`} className="text-xl leading-snug font-medium">
        {question.title}
      </h3>

      <div role="radiogroup" aria-labelledby={`${name}-title`} className="grid gap-3 sm:grid-cols-2">
        {question.options.map((option, index) => (
          <Option
            key={option.value}
            name={name}
            letter={letters[index]}
            label={option.label}
            checked={choice === option.value}
            onSelect={() => select(option.value)}
          />
        ))}
      </div>

      {askCertainty && !answer && (
        <div className="flex flex-col gap-3">
          <p className="font-medium">{reviewCopy.certaintyQuestion}</p>
          <div className="flex flex-wrap gap-2">
            {certainties.map((certainty) => (
              <Button
                key={certainty}
                variant="ghost"
                disabled={!choice}
                onClick={() => choice && reveal(choice, certainty)}
              >
                {reviewCopy.certainty[certainty]}
              </Button>
            ))}
          </div>
          {!choice && <p className="text-sm text-muted">{reviewCopy.pickFirst}</p>}
        </div>
      )}

      <div aria-live="polite">
        {answer && (
          <div className="flex flex-col gap-4">
            <div
              className={`flex flex-col gap-2 rounded-md border p-4 ${answer.correct ? "border-holds/60" : "border-middle/60"}`}
            >
              <p className={`font-medium ${answer.correct ? "text-holds" : "text-middle"}`}>{feedback()}</p>
              <p className="text-muted">{question.reason}</p>
              {!answer.correct && answer.certainty === "sure" && <p>{reviewCopy.sureAndWrong}</p>}
            </div>

            <details className="rounded-md border border-border bg-surface p-4">
              <summary className="cursor-pointer font-medium">{reviewCopy.whyInACrash}</summary>
              <p className="mt-3 text-muted">{question.whyInACrash}</p>
            </details>

            {afterReveal}

            <Button className="w-full sm:w-fit" onClick={onNext}>
              {isLast ? reviewCopy.finish : `${reviewCopy.next} →`}
            </Button>
          </div>
        )}
      </div>
    </div>
  );
}
