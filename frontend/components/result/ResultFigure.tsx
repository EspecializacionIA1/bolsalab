import { FigureBox } from "@/components/figure/FigureBox";
import { WireFigure } from "@/components/figure/WireFigure";
import { categoryColors } from "@/components/result/categoryColors";
import { questions } from "@/lib/content/diagnostic";
import { figure, type PartEffect, type ProfilePart } from "@/lib/content/result";
import type { Answers, Result } from "@/schemas/prediction";

const CORNERS: [ProfilePart, ProfilePart, ProfilePart] = ["knowledge", "situation", "confidence"];

const PART_OF: Record<string, ProfilePart> = {
  knows_interest: "knowledge",
  knows_inflation: "knowledge",
  knows_diversification: "knowledge",
  knowledge_confidence: "confidence",
  overconfidence: "confidence",
};

const effectColors: Record<PartEffect, { text: string; fill: string; dot: string }> = {
  increases: { text: "text-sells", fill: "fill-sells", dot: "bg-sells" },
  decreases: { text: "text-holds", fill: "fill-holds", dot: "bg-holds" },
  low: { text: "text-muted", fill: "fill-muted", dot: "bg-muted" },
};

function partEffect(result: Result, part: ProfilePart): PartEffect {
  const total = result.top_factors
    .filter((factor) => (PART_OF[factor.feature] ?? "situation") === part)
    .reduce((sum, factor) => sum + (factor.direction === "increases" ? factor.impact : -factor.impact), 0);
  if (total > 0) return "increases";
  if (total < 0) return "decreases";
  return "low";
}

function confidenceLabel(value?: number) {
  const question = questions.find((q) => q.field === "knowledge_confidence");
  if (!question || question.kind !== "choice") return "";
  return question.options.find((option) => option.value === value)?.label ?? "";
}

function partDetail(part: ProfilePart, result: Result, answers: Partial<Answers>) {
  const correct = 3 - result.failed_questions.length;
  if (part === "knowledge") return figure.details.knowledge(correct);
  if (part === "situation") return figure.details.situation;
  const answer = figure.details.confidence(confidenceLabel(answers.knowledge_confidence));
  return result.overconfident && correct < 3 ? `${answer} ${figure.details.confidenceHigh}` : answer;
}

type ResultFigureProps = {
  result: Result;
  answers: Partial<Answers>;
};

export function ResultFigure({ result, answers }: ResultFigureProps) {
  const style = categoryColors[result.category];
  const effects = CORNERS.map((part) => partEffect(result, part));
  const label = figure.label(
    CORNERS.map((part, index) => `${figure.parts[part].name.toLowerCase()}, ${figure.effects[effects[index]].toLowerCase()}`).join("; "),
  );

  return (
    <figure className="flex flex-col gap-4">
      <FigureBox className="w-full max-w-[180px] lg:max-w-none">
        <WireFigure
          pieceStroke={style.stroke}
          cornerFills={effects.map((effect) => effectColors[effect].fill) as [string, string, string]}
          label={label}
        />
      </FigureBox>
      <figcaption className="text-sm text-muted">{figure.caption}</figcaption>
      <ul className="flex flex-col gap-3">
        {CORNERS.map((part, index) => {
          const colors = effectColors[effects[index]];
          return (
            <li key={part} className="flex gap-3">
              <span aria-hidden className={`mt-1.5 size-2.5 shrink-0 rounded-full ${colors.dot}`} />
              <div className="flex flex-col gap-0.5 text-sm">
                <p>
                  <span className="font-mono text-xs text-muted uppercase">{figure.parts[part].position}</span>{" "}
                  <strong className="font-medium">{figure.parts[part].name}</strong>
                </p>
                <p className="text-muted">{partDetail(part, result, answers)}</p>
                <p className={`font-mono text-xs ${colors.text}`}>{figure.effects[effects[index]]}</p>
              </div>
            </li>
          );
        })}
      </ul>
    </figure>
  );
}
