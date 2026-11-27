"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { BeforeInvesting } from "@/components/plan/BeforeInvesting";
import { defaultRule, ruleSentence, suggestedActions } from "@/components/plan/rule";
import { RuleBuilder } from "@/components/plan/RuleBuilder";
import { Button } from "@/components/ui/Button";
import { Eyebrow } from "@/components/ui/Eyebrow";
import { useDiagnostic } from "@/context/DiagnosticContext";
import { pages } from "@/lib/content/pages";
import { planCopy } from "@/lib/content/plan";

export function PlanView() {
  const router = useRouter();
  const { answers, result, rule, ready, setRule } = useDiagnostic();

  if (!ready) return null;

  const current = rule ?? defaultRule(result, answers.assets_level);

  function openSummary() {
    setRule(current);
    router.push("/summary");
  }

  return (
    <main className="mx-auto w-full max-w-[1312px] px-4 py-12 md:px-8 md:py-16">
      <div className="flex max-w-3xl flex-col gap-8">
        {result && (
          <Link href="/result" className="w-fit text-sm text-primary underline-offset-4 hover:underline">
            {planCopy.back}
          </Link>
        )}
        <div className="flex flex-col gap-3">
          <Eyebrow>{pages.plan.name}</Eyebrow>
          <h1 className="text-4xl leading-tight font-medium tracking-[-0.02em] md:text-5xl">{pages.plan.title}</h1>
          <p className="text-lg text-muted">{pages.plan.description}</p>
        </div>

        <RuleBuilder rule={current} suggested={suggestedActions(result, answers.assets_level)} onChange={setRule} />

        {result && (
          <div className="flex flex-col items-start gap-2">
            <Button disabled={!ruleSentence(current)} onClick={openSummary}>
              {planCopy.summary}
            </Button>
            <p className="text-sm text-muted">{planCopy.privacy}</p>
          </div>
        )}

        <BeforeInvesting />
      </div>
    </main>
  );
}
