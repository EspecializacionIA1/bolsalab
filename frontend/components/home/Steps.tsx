import { Card } from "@/components/ui/Card";
import { steps } from "@/lib/content/home";

export function Steps() {
  return (
    <section className="mx-auto flex w-full max-w-[1312px] flex-col gap-6 px-4 pb-20 md:px-8">
      <h2 className="text-3xl leading-tight font-medium tracking-[-0.02em] md:text-[40px]">
        {steps.title}
      </h2>

      <ol className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
        {steps.items.map((step) => (
          <li key={step.number}>
            <Card className="flex h-full flex-col gap-3">
              <span className="font-mono text-[11px] tracking-[0.08em] text-primary">{step.number}</span>
              <h3 className="text-[22px] leading-tight font-medium">{step.title}</h3>
              <p className="text-sm leading-relaxed text-muted">{step.body}</p>
            </Card>
          </li>
        ))}
      </ol>
    </section>
  );
}
