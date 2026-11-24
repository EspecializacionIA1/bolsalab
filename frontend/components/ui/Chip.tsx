import type { ReactNode } from "react";

type ChipProps = {
  type: "radio" | "checkbox";
  name: string;
  checked: boolean;
  onChange: () => void;
  children: ReactNode;
};

export function Chip({ type, name, checked, onChange, children }: ChipProps) {
  const style = checked ? "border-primary bg-primary/10 text-foreground" : "border-border bg-surface text-muted hover:border-muted";

  return (
    <label
      className={`inline-flex min-h-11 cursor-pointer items-center gap-2 rounded-md border px-4 py-2 text-left transition-colors has-focus-visible:outline-2 has-focus-visible:outline-offset-2 has-focus-visible:outline-primary ${style}`}
    >
      <input type={type} name={name} checked={checked} onChange={onChange} className="sr-only" />
      {children}
    </label>
  );
}
