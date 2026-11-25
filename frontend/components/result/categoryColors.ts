import type { PieceShift } from "@/components/figure/WireFigure";
import type { Result } from "@/schemas/prediction";

type CategoryStyle = { text: string; bar: string; stroke: string; fill: string; shift: PieceShift };

export const categoryColors: Record<Result["category"], CategoryStyle> = {
  less_likely: { text: "text-holds", bar: "bg-holds", stroke: "stroke-holds", fill: "fill-holds", shift: "none" },
  similar: { text: "text-middle", bar: "bg-middle", stroke: "stroke-middle", fill: "fill-middle", shift: "small" },
  more_likely: { text: "text-sells", bar: "bg-sells", stroke: "stroke-sells", fill: "fill-sells", shift: "large" },
};
