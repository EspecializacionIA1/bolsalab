import type { ReactNode } from "react";

const tones = {
  neutral: { box: "border-border", title: "text-primary" },
  warning: { box: "border-middle/60", title: "text-middle" },
  error: { box: "border-sells/60", title: "text-sells" },
};

type NoticeProps = {
  title?: string;
  tone?: keyof typeof tones;
  children: ReactNode;
};

export function Notice({ title, tone = "neutral", children }: NoticeProps) {
  return (
    <div className={`flex flex-col gap-1 rounded-md border border-dashed p-4 text-sm ${tones[tone].box}`}>
      {title && <p className={`font-medium ${tones[tone].title}`}>{title}</p>}
      <div className="text-muted">{children}</div>
    </div>
  );
}
