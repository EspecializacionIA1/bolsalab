"use client";

import { useEffect, useRef, type ReactNode } from "react";
import { AgeInput } from "@/components/diagnostic/AgeInput";
import { Card } from "@/components/ui/Card";
import { Eyebrow } from "@/components/ui/Eyebrow";
import { Notice } from "@/components/ui/Notice";
import { Option } from "@/components/ui/Option";
import { Progress } from "@/components/ui/Progress";
import { blocks, navigation, questions, type Question } from "@/lib/content/diagnostic";
import type { Answers } from "@/schemas/prediction";

const letters = "ABCDE";

type AnswerValue = Answers[keyof Answers] | undefined;

type QuestionScreenProps = {
  question: Question;
  number: number;
  value: AnswerValue;
  onAnswer: (value: AnswerValue) => void;
  alert?: ReactNode;
  children: ReactNode;
};

export function QuestionScreen({ question, number, value, onAnswer, alert, children }: QuestionScreenProps) {
  const titleRef = useRef<HTMLHeadingElement>(null);
  const block = blocks[question.block];
  const progressLabel = navigation.progress(number, questions.length, block.title);

  useEffect(() => {
    titleRef.current?.focus({ preventScroll: true });
  }, []);

  return (
    <main className="mx-auto flex w-full max-w-[1312px] flex-col gap-8 px-4 py-8 md:px-8 lg:gap-10">
      <div className="flex flex-col gap-3">
        <p className="font-mono text-xs tracking-[0.06em] text-muted uppercase">{progressLabel}</p>
        <Progress current={number} total={questions.length} label={progressLabel} />
      </div>

      {alert}

      <div className="grid gap-8 lg:grid-cols-[minmax(0,1fr)_380px] lg:gap-16">
        <section className="flex min-w-0 flex-col gap-6">
          <h1
            ref={titleRef}
            id="question-title"
            tabIndex={-1}
            className="text-3xl leading-[1.15] font-medium tracking-[-0.02em] outline-none md:text-[40px]"
          >
            {question.title}
          </h1>

          {block.intro && !question.hideBlockIntro && <p className="text-lg text-muted">{block.intro}</p>}

          {question.kind === "number" ? (
            <AgeInput
              min={question.min}
              max={question.max}
              value={typeof value === "number" ? value : undefined}
              onChange={onAnswer}
            />
          ) : (
            <div role="radiogroup" aria-labelledby="question-title" className="grid gap-3 sm:grid-cols-2">
              {question.options.map((option, index) => (
                <Option
                  key={option.label}
                  name={question.field}
                  letter={letters[index]}
                  label={option.label}
                  checked={value === option.value}
                  onSelect={() => onAnswer(option.value)}
                />
              ))}
            </div>
          )}

          {children}
        </section>

        <aside className="flex flex-col gap-4">
          <Card className="flex flex-col gap-2">
            <Eyebrow>{navigation.why}</Eyebrow>
            <p>{question.why}</p>
          </Card>
          {block.note && <Notice>{block.note}</Notice>}
        </aside>
      </div>
    </main>
  );
}
