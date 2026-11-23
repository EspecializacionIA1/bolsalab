import type { ComponentProps } from "react";

export function Card({ className = "", ...props }: ComponentProps<"div">) {
  return <div className={`rounded-md border border-border bg-surface p-5 ${className}`} {...props} />;
}
