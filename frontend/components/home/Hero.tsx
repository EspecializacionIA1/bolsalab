import { FigureBox } from "@/components/figure/FigureBox";
import { WireFigure } from "@/components/figure/WireFigure";
import { ButtonLink } from "@/components/ui/Button";
import { mainCta } from "@/lib/content/general";
import { hero } from "@/lib/content/home";

export function Hero() {
  return (
    <section className="mx-auto grid w-full max-w-[1312px] items-center gap-12 px-4 pt-16 pb-14 md:px-8 md:pt-24 lg:grid-cols-[minmax(0,1fr)_420px]">
      <div className="flex flex-col items-start gap-6">
        <h1 className="text-[40px] leading-[1.06] font-medium tracking-[-0.03em] sm:text-5xl lg:text-[64px]">
          {hero.title}{" "}
          <span className="bg-linear-to-r from-primary to-holds bg-clip-text text-transparent">{hero.highlight}</span>.
        </h1>

        <p className="max-w-2xl text-lg text-muted">{hero.body}</p>

        <div className="flex w-full flex-col gap-3 sm:w-auto sm:flex-row">
          <ButtonLink href={mainCta.href}>{mainCta.label} →</ButtonLink>
          <ButtonLink href={hero.secondaryCta.href} variant="ghost">
            {hero.secondaryCta.label}
          </ButtonLink>
        </div>

        <ul className="flex flex-wrap gap-2">
          {hero.facts.map((fact) => (
            <li key={fact} className="rounded-sm border border-border bg-surface px-3 py-1.5 font-mono text-xs text-muted">
              {fact}
            </li>
          ))}
        </ul>
      </div>

      <FigureBox className="hidden lg:block">
        <WireFigure />
      </FigureBox>
    </section>
  );
}
