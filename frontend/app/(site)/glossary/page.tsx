import type { Metadata } from "next";
import { GlossaryView } from "@/components/glossary/GlossaryView";
import { pages } from "@/lib/content/pages";

export const metadata: Metadata = { title: pages.glossary.name };

export default function GlossaryPage() {
  return <GlossaryView />;
}
