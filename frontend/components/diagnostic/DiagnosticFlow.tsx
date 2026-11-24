"use client";

import { useState } from "react";
import { DiagnosticIntro } from "@/components/diagnostic/DiagnosticIntro";
import { Questionnaire } from "@/components/diagnostic/Questionnaire";
import { useDiagnostic } from "@/context/DiagnosticContext";

export function DiagnosticFlow() {
  const { answers, ready } = useDiagnostic();
  const [started, setStarted] = useState(false);

  if (!ready) return null;

  if (!started && Object.keys(answers).length === 0) {
    return <DiagnosticIntro onStart={() => setStarted(true)} />;
  }

  return <Questionnaire />;
}
