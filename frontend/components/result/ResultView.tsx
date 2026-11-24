"use client";

import { useRouter } from "next/navigation";
import { useEffect } from "react";
import { categoryColors } from "@/components/result/categoryColors";
import { TercileBar } from "@/components/result/TercileBar";
import { Button } from "@/components/ui/Button";
import { Eyebrow } from "@/components/ui/Eyebrow";
import { Notice } from "@/components/ui/Notice";
import { useDiagnostic } from "@/context/DiagnosticContext";
import { comparison, headlines, meaning, restart } from "@/lib/content/result";

export function ResultView() {
  const router = useRouter();
  const { result, ready, reset } = useDiagnostic();

  useEffect(() => {
    if (ready && !result) router.replace("/diagnostic");
  }, [ready, result, router]);

  if (!result) return null;

  const headline = headlines[result.category];
  const color = categoryColors[result.category].text;

  return (
    <main className="mx-auto w-full max-w-[1312px] px-4 py-12 md:px-8 md:py-20">
      <div className="flex max-w-3xl flex-col gap-6">
        <Eyebrow className={color}>{headline.label}</Eyebrow>
        <h1 className="text-4xl leading-tight font-medium tracking-[-0.02em] md:text-5xl">
          {headline.title} <span className={color}>{headline.highlight}</span>.
        </h1>
        <p className="text-lg text-muted">{headline.body}</p>

        <TercileBar category={result.category} />

        <dl className="grid gap-4 sm:grid-cols-2">
          {meaning.map((item) => (
            <div key={item.title} className="flex flex-col gap-1 border-l-2 border-border pl-4">
              <dt className="font-medium">{item.title}</dt>
              <dd className="text-muted">{item.body}</dd>
            </div>
          ))}
        </dl>

        <Notice>{comparison}</Notice>
        <Button variant="ghost" className="w-full sm:w-fit" onClick={reset}>
          {restart}
        </Button>
      </div>
    </main>
  );
}
