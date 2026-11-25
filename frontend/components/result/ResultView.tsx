"use client";

import { useRouter } from "next/navigation";
import { useEffect } from "react";
import { AgeWarnings } from "@/components/result/AgeWarnings";
import { categoryColors } from "@/components/result/categoryColors";
import { FactorsSection } from "@/components/result/FactorsSection";
import { NextStep } from "@/components/result/NextStep";
import { ResultFigure } from "@/components/result/ResultFigure";
import { ReviewSection } from "@/components/result/review/ReviewSection";
import { TercileBar } from "@/components/result/TercileBar";
import { Button } from "@/components/ui/Button";
import { Eyebrow } from "@/components/ui/Eyebrow";
import { Notice } from "@/components/ui/Notice";
import { useDiagnostic } from "@/context/DiagnosticContext";
import { comparison, headlines, meaning, restart } from "@/lib/content/result";

export function ResultView() {
  const router = useRouter();
  const { answers, result, ready, reset } = useDiagnostic();

  useEffect(() => {
    if (ready && !result) router.replace("/diagnostic");
  }, [ready, result, router]);

  if (!result) return null;

  const headline = headlines[result.category];
  const color = categoryColors[result.category].text;

  return (
    <main className="mx-auto grid w-full max-w-[1312px] gap-8 px-4 py-12 md:px-8 md:py-20 lg:grid-cols-[minmax(0,48rem)_300px] lg:items-start lg:gap-16">
      <aside className="order-first lg:sticky lg:top-8 lg:order-last">
        <ResultFigure category={result.category} />
      </aside>
      <div className="flex min-w-0 flex-col gap-6">
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

        <AgeWarnings age={answers.age} warnings={result.warnings} />

        <FactorsSection factors={result.top_factors} />

        <ReviewSection result={result} answers={answers} />

        <NextStep />

        <Button variant="ghost" className="w-full sm:w-fit" onClick={reset}>
          {restart}
        </Button>
      </div>
    </main>
  );
}
