"use client";

import { useState } from "react";
import { QuestionNav } from "@/components/diagnostic/QuestionNav";
import { QuestionScreen } from "@/components/diagnostic/QuestionScreen";
import { useDiagnostic } from "@/context/DiagnosticContext";
import { questions } from "@/lib/content/diagnostic";
import type { Answers } from "@/schemas/prediction";

function firstUnanswered(answers: Partial<Answers>) {
  const index = questions.findIndex((question) => answers[question.field] === undefined);
  return index === -1 ? questions.length - 1 : index;
}

export function Questionnaire() {
  const { answers, setAnswer } = useDiagnostic();
  const [index, setIndex] = useState(() => firstUnanswered(answers));
  const question = questions[index];
  const isLast = index === questions.length - 1;

  function goTo(newIndex: number) {
    setIndex(newIndex);
    window.scrollTo(0, 0);
  }

  return (
    <QuestionScreen
      key={question.field}
      question={question}
      number={index + 1}
      value={answers[question.field]}
      onAnswer={(value) => setAnswer(question.field, value)}
    >
      <QuestionNav
        showBack={index > 0}
        isLast={isLast}
        canContinue={answers[question.field] !== undefined}
        onBack={() => goTo(index - 1)}
        onNext={() => {
          if (!isLast) goTo(index + 1);
        }}
      />
    </QuestionScreen>
  );
}
