import { Card } from "@/components/ui/Card";
import { Eyebrow } from "@/components/ui/Eyebrow";
import { howItWorks } from "@/lib/content/howItWorks";
import { pages } from "@/lib/content/pages";

const sectionStyle = "flex flex-col gap-5 border-t border-border pt-10";
const titleStyle = "text-2xl font-medium tracking-[-0.01em] md:text-3xl";

export function HowItWorksView() {
  const { data, accuracy, limits, privacy, team } = howItWorks;

  return (
    <main className="mx-auto w-full max-w-[1312px] px-4 py-12 md:px-8 md:py-16">
      <div className="flex max-w-3xl flex-col gap-10">
        <div className="flex flex-col gap-3">
          <Eyebrow>{pages.howItWorks.name}</Eyebrow>
          <h1 className="text-4xl leading-tight font-medium tracking-[-0.02em] md:text-5xl">{pages.howItWorks.title}</h1>
          <p className="text-lg text-muted">{pages.howItWorks.description}</p>
        </div>

        <section aria-labelledby="data-title" className={sectionStyle}>
          <h2 id="data-title" className={titleStyle}>
            {data.title}
          </h2>
          <p className="flex flex-col">
            <span className="font-mono text-5xl text-primary">{data.number}</span>
            <span className="text-muted">{data.numberLabel}</span>
          </p>
          <p>{data.body}</p>
          <p>{data.how}</p>
          <p className="text-sm text-muted">{data.source}</p>
        </section>

        <section aria-labelledby="accuracy-title" className={sectionStyle}>
          <h2 id="accuracy-title" className={titleStyle}>
            {accuracy.title}
          </h2>
          <p>{accuracy.intro}</p>
          <ul className="grid gap-3 sm:grid-cols-3">
            {accuracy.cards.map((card) => (
              <li key={card.label}>
                <Card className="flex h-full flex-col gap-2">
                  <span className="font-mono text-2xl text-primary">{card.value}</span>
                  <span className="font-medium">{card.label}</span>
                  {card.note && <span className="text-sm text-muted">{card.note}</span>}
                </Card>
              </li>
            ))}
          </ul>
          <p className="text-muted">{accuracy.closing}</p>
        </section>

        <section aria-labelledby="limits-title" className={sectionStyle}>
          <h2 id="limits-title" className={titleStyle}>
            {limits.title}
          </h2>
          <ul className="flex flex-col gap-3">
            {limits.items.map((item) => (
              <li key={item.lead} className="border-l-2 border-middle/60 pl-4">
                <strong className="font-medium">{item.lead}</strong> <span className="text-muted">{item.text}</span>
              </li>
            ))}
          </ul>
        </section>

        <section aria-labelledby="privacy-title" className={sectionStyle}>
          <h2 id="privacy-title" className={titleStyle}>
            {privacy.title}
          </h2>
          <ul className="flex list-disc flex-col gap-2 pl-5 text-muted marker:text-primary">
            {privacy.items.map((item) => (
              <li key={item}>{item}</li>
            ))}
          </ul>
        </section>

        <p className="border-t border-border pt-8 text-sm text-muted">{team}</p>
      </div>
    </main>
  );
}
