import Link from "next/link";
import { brand } from "@/lib/content/general";

export function Logo({ tag = brand.tag }: { tag?: string }) {
  return (
    <Link href="/" className="flex items-center gap-3 rounded-sm">
      <svg viewBox="0 0 26 28" className="h-7 w-[26px] fill-none stroke-[1.5]" aria-hidden="true">
        <path d="M13 2 24 8.5v11L13 26 2 19.5v-11L13 2Z" className="stroke-primary" />
        <path d="M13 9l5 8H8l5-8Z" className="stroke-holds" />
      </svg>
      <span className="text-xl font-medium tracking-[-0.01em]">{brand.name}</span>
      <span className="rounded-sm border border-border bg-surface-raised px-2.5 py-1.5 font-mono text-xs leading-none">
        {tag}
      </span>
    </Link>
  );
}
