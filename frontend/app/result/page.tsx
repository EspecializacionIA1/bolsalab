import type { Metadata } from "next";
import { ResultView } from "@/components/result/ResultView";
import { pages } from "@/lib/content/pages";

export const metadata: Metadata = { title: pages.result.name };

export default function ResultPage() {
  return <ResultView />;
}
