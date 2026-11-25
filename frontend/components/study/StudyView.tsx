import Link from "next/link";
import { Card } from "@/components/ui/Card";
import { Eyebrow } from "@/components/ui/Eyebrow";
import { Notice } from "@/components/ui/Notice";
import { pages } from "@/lib/content/pages";
import { groupSets, studyCopy } from "@/lib/content/study";

function perHundred(rate: number) {
  return Math.round(rate * 100);
}

function GroupBar({ label, soldRate }: { label: string; soldRate: number }) {
  const value = perHundred(soldRate);
  return (
    <li className="flex flex-col gap-1.5">
      <div className="flex items-baseline justify-between gap-4">
        <span>{label}</span>
        <span className="font-mono text-sm text-primary">
          {value} {studyCopy.ofHundred}
        </span>
      </div>
      <span aria-hidden className="h-2 rounded-[1px] bg-surface-raised">
        <span className="block h-full rounded-[1px] bg-primary" style={{ width: `${value}%` }} />
      </span>
    </li>
  );
}

export function StudyView() {
  const { everyone } = studyCopy;

  return (
    <main className="mx-auto w-full max-w-[1312px] px-4 py-12 md:px-8 md:py-16">
      <div className="flex max-w-3xl flex-col gap-10">
        <div className="flex flex-col gap-3">
          <Eyebrow>{pages.study.name}</Eyebrow>
          <h1 className="text-4xl leading-tight font-medium tracking-[-0.02em] md:text-5xl">{pages.study.title}</h1>
          <p className="text-lg text-muted">{pages.study.description}</p>
          <p className="text-muted">{studyCopy.intro}</p>
        </div>

        <section aria-labelledby="everyone-title" className="flex flex-col gap-4 border-t border-border pt-10">
          <h2 id="everyone-title" className="text-xl font-medium">
            {studyCopy.question}
          </h2>
          <p className="flex flex-col">
            <span className="font-mono text-5xl text-primary">
              {perHundred(everyone.soldRate)} {studyCopy.ofHundred}
            </span>
            <span className="text-muted">
              {everyone.label}. {everyone.finding}
            </span>
          </p>
        </section>

        <div className="grid gap-4 sm:grid-cols-2">
          {groupSets.map((set) => (
            <Card key={set.title} className="flex flex-col gap-4">
              <h2 className="font-medium">{set.title}</h2>
              <ul className="flex flex-col gap-3">
                {set.groups.map((group) => (
                  <GroupBar key={group.label} label={group.label} soldRate={group.soldRate} />
                ))}
              </ul>
              <p className="text-sm text-muted">{set.finding}</p>
            </Card>
          ))}
        </div>

        <p className="text-sm text-muted">{studyCopy.beginnersNote}</p>

        <Notice>{studyCopy.caveat}</Notice>

        <div className="flex flex-col gap-2 border-t border-border pt-8">
          <Link href={studyCopy.accuracyLink.href} className="w-fit text-primary underline-offset-4 hover:underline">
            {studyCopy.accuracyLink.label}
          </Link>
          <p className="text-sm text-muted">{studyCopy.source}</p>
        </div>
      </div>
    </main>
  );
}
