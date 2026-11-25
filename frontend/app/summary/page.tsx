import type { Metadata } from "next";
import { SummaryView } from "@/components/summary/SummaryView";
import { summaryCopy } from "@/lib/content/summary";

export const metadata: Metadata = { title: summaryCopy.name };

export default function SummaryPage() {
  return <SummaryView />;
}
