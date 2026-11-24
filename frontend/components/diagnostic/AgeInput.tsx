"use client";

import { useState, type ChangeEvent } from "react";
import { navigation } from "@/lib/content/diagnostic";

type AgeInputProps = {
  min: number;
  max: number;
  value?: number;
  onChange: (age: number | undefined) => void;
};

function readAge(text: string, min: number, max: number) {
  const age = Number(text);
  return text !== "" && age >= min && age <= max ? age : undefined;
}

export function AgeInput({ min, max, value, onChange }: AgeInputProps) {
  const [text, setText] = useState(value?.toString() ?? "");

  function handleChange(event: ChangeEvent<HTMLInputElement>) {
    const digits = event.target.value.replace(/\D/g, "");
    setText(digits);
    onChange(readAge(digits, min, max));
  }

  return (
    <label className="flex flex-col gap-2 text-sm text-muted">
      {navigation.ageLabel}
      <input
        inputMode="numeric"
        autoComplete="off"
        maxLength={3}
        value={text}
        onChange={handleChange}
        className="h-[75px] w-full max-w-[200px] rounded-md border border-border bg-surface px-5 font-mono text-2xl text-foreground transition-colors hover:border-muted focus:border-primary"
      />
    </label>
  );
}
