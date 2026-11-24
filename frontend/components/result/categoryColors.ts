import type { Result } from "@/schemas/prediction";

export const categoryColors: Record<Result["category"], { text: string; bar: string }> = {
  less_likely: { text: "text-holds", bar: "bg-holds" },
  similar: { text: "text-middle", bar: "bg-middle" },
  more_likely: { text: "text-sells", bar: "bg-sells" },
};
