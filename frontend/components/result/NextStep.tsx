import { ButtonLink } from "@/components/ui/Button";
import { Eyebrow } from "@/components/ui/Eyebrow";
import { nextStep } from "@/lib/content/result";

export function NextStep() {
  return (
    <section
      aria-labelledby="next-step-title"
      className="flex flex-col items-start gap-3 rounded-md border border-primary/60 bg-primary/5 p-6"
    >
      <Eyebrow>{nextStep.label}</Eyebrow>
      <h2 id="next-step-title" className="text-2xl font-medium tracking-[-0.01em]">
        {nextStep.title}
      </h2>
      <p className="text-muted">{nextStep.body}</p>
      <ButtonLink href={nextStep.href} className="w-full sm:w-fit">
        {nextStep.action} →
      </ButtonLink>
    </section>
  );
}
