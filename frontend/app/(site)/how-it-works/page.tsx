import type { Metadata } from "next";
import { PagePlaceholder } from "@/components/layout/PagePlaceholder";
import { pages } from "@/lib/content/pages";

export const metadata: Metadata = { title: pages.howItWorks.name };

export default function HowItWorksPage() {
  return <PagePlaceholder page={pages.howItWorks} />;
}
