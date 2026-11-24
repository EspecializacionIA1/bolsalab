"use client";

import { createContext, use, useEffect, useReducer, type ReactNode } from "react";
import type { Answers, Result } from "@/schemas/prediction";
import {
  emptyDiagnostic,
  loadDiagnostic,
  saveDiagnostic,
  type SavedDiagnostic,
} from "@/services/diagnostic-storage";

type State = SavedDiagnostic & { ready: boolean };

type Action =
  | { type: "load"; saved: SavedDiagnostic }
  | { type: "answer"; answers: Partial<Answers> }
  | { type: "result"; result: Result }
  | { type: "reset" };

type DiagnosticContextValue = State & {
  setAnswer: <Field extends keyof Answers>(field: Field, value: Answers[Field] | undefined) => void;
  setResult: (result: Result) => void;
  reset: () => void;
};

const DiagnosticContext = createContext<DiagnosticContextValue | null>(null);

function reducer(state: State, action: Action): State {
  switch (action.type) {
    case "load":
      return { ...action.saved, ready: true };
    case "answer":
      return { ...state, answers: { ...state.answers, ...action.answers }, result: null };
    case "result":
      return { ...state, result: action.result };
    case "reset":
      return { ...emptyDiagnostic, ready: true };
  }
}

export function DiagnosticProvider({ children }: { children: ReactNode }) {
  const [state, dispatch] = useReducer(reducer, { ...emptyDiagnostic, ready: false });
  const { answers, result, ready } = state;

  useEffect(() => {
    dispatch({ type: "load", saved: loadDiagnostic() });
  }, []);

  useEffect(() => {
    if (ready) saveDiagnostic({ answers, result });
  }, [answers, result, ready]);

  const value: DiagnosticContextValue = {
    ...state,
    setAnswer: (field, answer) => dispatch({ type: "answer", answers: { [field]: answer } }),
    setResult: (newResult) => dispatch({ type: "result", result: newResult }),
    reset: () => dispatch({ type: "reset" }),
  };

  return <DiagnosticContext value={value}>{children}</DiagnosticContext>;
}

export function useDiagnostic(): DiagnosticContextValue {
  const context = use(DiagnosticContext);
  if (!context) throw new Error("useDiagnostic debe usarse dentro de DiagnosticProvider");
  return context;
}
