"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useEffect, useRef } from "react";
import { FigureBox } from "@/components/figure/FigureBox";
import { WireFigure } from "@/components/figure/WireFigure";
import { ruleSentence } from "@/components/plan/rule";
import { ageMessages } from "@/components/result/AgeWarnings";
import { categoryColors } from "@/components/result/categoryColors";
import { FactorList } from "@/components/result/FactorList";
import { TercileBar } from "@/components/result/TercileBar";
import { SummaryCard } from "@/components/summary/SummaryCard";
import { Button } from "@/components/ui/Button";
import { Eyebrow } from "@/components/ui/Eyebrow";
import { useDiagnostic } from "@/context/DiagnosticContext";
import { knowledgeFields, knowledgeTopics, reviewQuestions } from "@/lib/content/quiz";
import { factorsCopy, headlines } from "@/lib/content/result";
import { checklistShort, summaryCopy } from "@/lib/content/summary";

const linkStyle = "w-fit text-sm text-primary underline-offset-4 hover:underline print:hidden";

export function SummaryView() {
  const router = useRouter();
  const clearing = useRef(false);
  const { answers, result, rule, ready, reset } = useDiagnostic();

  useEffect(() => {
    if (ready && !result && !clearing.current) router.replace("/diagnostic");
  }, [ready, result, router]);

  if (!result) return null;

  const headline = headlines[result.category];
  const style = categoryColors[result.category];
  const sentence = rule ? ruleSentence(rule) : null;
  const failed = knowledgeFields.filter((field) => result.failed_questions.includes(field));
  const showReview = failed.length > 0 || result.overconfident;
  const actionable = result.top_factors.filter((factor) => factor.actionable);
  const situation = result.top_factors.filter((factor) => !factor.actionable);
  const maxImpact = Math.max(...result.top_factors.map((factor) => factor.impact));
  const warnings = ageMessages(answers.age, result.warnings);
  const today = new Date().toLocaleDateString("es-CO", { day: "numeric", month: "long", year: "numeric" });

  function clear() {
    clearing.current = true;
    reset();
    router.push("/");
  }

  return (
    <main className="mx-auto w-full max-w-[1312px] px-4 py-12 md:px-8 md:py-16 print:p-0">
      <article id="summary-sheet" aria-labelledby="summary-title" className="flex max-w-5xl flex-col gap-6 print:gap-3">
        <p className="hidden border-b border-border pb-2 text-sm print:block">
          {summaryCopy.printedTitle} · {today}
        </p>

        <div className="flex flex-col gap-3 print:hidden">
          <Link href="/plan" className={linkStyle}>
            {summaryCopy.back}
          </Link>
          <Eyebrow>{summaryCopy.name}</Eyebrow>
          <h1 id="summary-title" className="text-4xl leading-tight font-medium tracking-[-0.02em] md:text-5xl">
            {summaryCopy.title}
          </h1>
          <p className="text-lg text-muted">{summaryCopy.intro}</p>
          <div className="mt-2 flex flex-col items-start gap-2">
            <Button onClick={() => window.print()}>{summaryCopy.print}</Button>
            <p className="max-w-2xl text-sm text-muted">{summaryCopy.printNote}</p>
          </div>
        </div>

        <div className="grid gap-4 md:grid-cols-2 print:grid-cols-2 print:gap-3">
          <SummaryCard id="card-tercile" title={summaryCopy.cards.tercile}>
            <div className="flex items-start justify-between gap-4">
              <div className="flex flex-col gap-1">
                <p className={`font-mono text-[11px] tracking-[0.06em] uppercase ${style.text}`}>{headline.label}</p>
                <p className="text-xl leading-snug font-medium print:text-base">
                  {headline.title} <span className={style.text}>{headline.highlight}</span>.
                </p>
              </div>
              <FigureBox className="w-20 shrink-0 print:hidden">
                <WireFigure shift={style.shift} pieceStroke={style.stroke} pieceFill={style.fill} />
              </FigureBox>
            </div>
            <TercileBar category={result.category} />
            <ul className="flex flex-col gap-1 text-sm text-muted">
              {summaryCopy.meaning.map((item) => (
                <li key={item.title}>
                  <strong className="font-medium text-foreground">{item.title}</strong> {item.body}
                </li>
              ))}
            </ul>
          </SummaryCard>

          <SummaryCard id="card-rule" title={summaryCopy.cards.rule} className="border-primary/60 bg-primary/5">
            {sentence ? (
              <p className="text-xl leading-snug print:text-base">{sentence}</p>
            ) : (
              <p className="text-muted">{summaryCopy.noRule}</p>
            )}
            <p className="text-sm text-muted">{summaryCopy.ruleNote}</p>
            <Link href="/plan" className={linkStyle}>
              {sentence ? summaryCopy.changeRule : summaryCopy.makeRule}
            </Link>
          </SummaryCard>

          <SummaryCard id="card-factors" title={summaryCopy.cards.factors}>
            {actionable.length > 0 && (
              <div className="flex flex-col gap-2">
                <h3 className="text-sm font-medium">{factorsCopy.actionable.title}</h3>
                <FactorList factors={actionable} maxImpact={maxImpact} />
              </div>
            )}
            {situation.length > 0 && (
              <div className="flex flex-col gap-2">
                <h3 className="text-sm font-medium">{factorsCopy.situation.title}</h3>
                <FactorList factors={situation} maxImpact={maxImpact} />
              </div>
            )}
            <p className="text-sm text-muted">{summaryCopy.factorsNote}</p>
          </SummaryCard>

          {showReview && (
            <SummaryCard id="card-review" title={summaryCopy.cards.review}>
              <ul className="flex flex-col gap-2 text-sm">
                {failed.map((field) => (
                  <li key={field}>
                    <strong className="font-medium">{knowledgeTopics[field]}.</strong>{" "}
                    <span className="text-muted">{reviewQuestions[field].reason}</span>
                  </li>
                ))}
                {result.overconfident && <li className="text-muted">{summaryCopy.overconfidence}</li>}
              </ul>
            </SummaryCard>
          )}

          <SummaryCard id="card-checklist" title={summaryCopy.cards.checklist} className="md:col-span-2 print:col-span-2">
            <ul className="grid gap-2 text-sm sm:grid-cols-2 print:grid-cols-2 print:gap-1">
              {checklistShort.map((item) => (
                <li key={item} className="flex items-start gap-2">
                  <span aria-hidden className="mt-0.5 size-4 shrink-0 rounded-[2px] border border-muted" />
                  {item}
                </li>
              ))}
            </ul>
            <Link href="/plan" className={linkStyle}>
              {summaryCopy.checklistMore}
            </Link>
          </SummaryCard>

          <SummaryCard id="card-read" title={summaryCopy.cards.howToRead} className="md:col-span-2 print:col-span-2">
            <p className="text-sm text-muted">{summaryCopy.howToRead}</p>
            {warnings.map((message) => (
              <p key={message} className="text-sm text-middle">
                {message}
              </p>
            ))}
          </SummaryCard>
        </div>

        <p className="hidden border-t border-border pt-2 text-xs print:block">{summaryCopy.printedFooter}</p>

        <div className="flex flex-col items-start gap-2 border-t border-border pt-8 print:hidden">
          <Button variant="ghost" onClick={clear}>
            {summaryCopy.clear}
          </Button>
          <p className="text-sm text-muted">{summaryCopy.clearNote}</p>
        </div>
      </article>
    </main>
  );
}
