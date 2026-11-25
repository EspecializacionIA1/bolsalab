import type { Metadata } from "next";
import { HowItWorksView } from "@/components/how-it-works/HowItWorksView";
import { pages } from "@/lib/content/pages";

export const metadata: Metadata = { title: pages.howItWorks.name };

export default function HowItWorksPage() {
  return <HowItWorksView />;
}
