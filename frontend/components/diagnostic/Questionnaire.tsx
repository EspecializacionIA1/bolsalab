"use client";

import { useRouter } from "next/navigation";
import { useState } from "react";
import { Calculating } from "@/components/diagnostic/Calculating";
import { QuestionNav } from "@/components/diagnostic/QuestionNav";
import { QuestionScreen } from "@/components/diagnostic/QuestionScreen";
import { SubmitError } from "@/components/diagnostic/SubmitError";
import { useDiagnostic } from "@/context/DiagnosticContext";
import { questions } from "@/lib/content/diagnostic";
import type { Answers } from "@/schemas/prediction";
import { ApiError } from "@/services/api-client";
import { predict } from "@/services/prediction-service";

const MIN_CALCULATING_MS = 1000;

function firstUnanswered(answers: Partial<Answers>) {
  const index = questions.findIndex((question) => answers[question.field] === undefined);
  return index === -1 ? questions.length - 1 : index;
}

function wait(ms: number) {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

export function Questionnaire() {
  const router = useRouter();
  const { answers, setAnswer, setResult } = useDiagnostic();
  const [index, setIndex] = useState(() => firstUnanswered(answers));
  const [sending, setSending] = useState(false);
  const [error, setError] = useState<ApiError | null>(null);
  const question = questions[index];
  const isLast = index === questions.length - 1;

  function goTo(newIndex: number) {
    setError(null);
    setIndex(newIndex);
    window.scrollTo(0, 0);
  }

  async function finish() {
    setError(null);
    setSending(true);
    window.scrollTo(0, 0);
    try {
      const [result] = await Promise.all([predict(answers), wait(MIN_CALCULATING_MS)]);
      setResult(result);
      router.push("/result");
    } catch (caught) {
      setError(caught instanceof ApiError ? caught : new ApiError("server"));
      setSending(false);
    }
  }

  function handleErrorAction() {
    if (error?.kind !== "validation") {
      finish();
      return;
    }
    const target = questions.findIndex((item) => error.fields.includes(item.field));
    if (target === -1) setError(null);
    else goTo(target);
  }

  if (sending) return <Calculating />;

  return (
    <QuestionScreen
      key={question.field}
      question={question}
      number={index + 1}
      value={answers[question.field]}
      onAnswer={(value) => {
        setError(null);
        setAnswer(question.field, value);
      }}
      alert={error && <SubmitError kind={error.kind} onAction={handleErrorAction} />}
    >
      <QuestionNav
        showBack={index > 0}
        isLast={isLast}
        canContinue={answers[question.field] !== undefined}
        onBack={() => goTo(index - 1)}
        onNext={() => (isLast ? finish() : goTo(index + 1))}
      />
    </QuestionScreen>
  );
}
