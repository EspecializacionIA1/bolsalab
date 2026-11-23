import Link from "next/link";
import type { ComponentProps } from "react";

const base =
  "inline-flex h-[46px] items-center justify-center gap-2 rounded-md px-5 font-mono text-[13px] " +
  "tracking-[0.06em] whitespace-nowrap uppercase transition-colors " +
  "disabled:cursor-not-allowed disabled:opacity-40";

const variants = {
  primary: "bg-primary text-on-primary hover:bg-primary/85",
  ghost: "border border-muted/50 text-foreground hover:border-foreground",
};

type Variant = keyof typeof variants;

type ButtonProps = ComponentProps<"button"> & { variant?: Variant };

export function Button({ variant = "primary", className = "", ...props }: ButtonProps) {
  return <button type="button" className={`${base} ${variants[variant]} ${className}`} {...props} />;
}

type ButtonLinkProps = ComponentProps<typeof Link> & { variant?: Variant };

export function ButtonLink({ variant = "primary", className = "", ...props }: ButtonLinkProps) {
  return <Link className={`${base} ${variants[variant]} ${className}`} {...props} />;
}
