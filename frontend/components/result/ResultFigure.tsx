import { FigureBox } from "@/components/figure/FigureBox";
import { WireFigure } from "@/components/figure/WireFigure";
import { categoryColors } from "@/components/result/categoryColors";
import { figure } from "@/lib/content/result";
import type { Result } from "@/schemas/prediction";

export function ResultFigure({ category }: { category: Result["category"] }) {
  const style = categoryColors[category];

  return (
    <figure className="flex flex-col gap-3">
      <FigureBox className="w-full max-w-[180px] lg:max-w-none">
        <WireFigure shift={style.shift} pieceStroke={style.stroke} pieceFill={style.fill} label={figure.labels[category]} />
      </FigureBox>
      <figcaption className="text-sm text-muted">{figure.caption}</figcaption>
    </figure>
  );
}
