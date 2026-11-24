import { Button } from "@/components/ui/Button";
import { Card } from "@/components/ui/Card";
import { Eyebrow } from "@/components/ui/Eyebrow";
import { Notice } from "@/components/ui/Notice";
import { blocks, intro, questions, type BlockId } from "@/lib/content/diagnostic";
import { pages } from "@/lib/content/pages";

const blockIds = Object.keys(blocks) as BlockId[];

function countQuestions(block: BlockId) {
  return questions.filter((question) => question.block === block).length;
}

export function DiagnosticIntro({ onStart }: { onStart: () => void }) {
  return (
    <main className="mx-auto w-full max-w-[1312px] px-4 py-12 md:px-8 md:py-20">
      <div className="flex max-w-3xl flex-col gap-6">
        <Eyebrow>{pages.diagnostic.name}</Eyebrow>
        <h1 className="text-4xl leading-tight font-medium tracking-[-0.02em] md:text-5xl">{intro.title}</h1>
        <p className="text-lg text-muted">{intro.body}</p>

        <ol className="grid gap-3 sm:grid-cols-3">
          {blockIds.map((id, index) => (
            <li key={id}>
              <Card className="flex h-full flex-col gap-2">
                <Eyebrow className="text-muted">
                  {intro.blockLabel} 0{index + 1}
                </Eyebrow>
                <p className="flex-1 font-medium">{blocks[id].title}</p>
                <p className="font-mono text-xs text-holds">
                  {countQuestions(id)} {intro.questionsLabel}
                </p>
              </Card>
            </li>
          ))}
        </ol>

        <Notice>{intro.privacy}</Notice>

        <Button className="w-full sm:w-fit" onClick={onStart}>
          {intro.start} →
        </Button>
      </div>
    </main>
  );
}
