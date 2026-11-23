import type { ComponentProps } from "react";

export function Eyebrow({ className = "text-primary", ...props }: ComponentProps<"p">) {
  return <p className={`font-mono text-[11px] tracking-[0.08em] uppercase ${className}`} {...props} />;
}
