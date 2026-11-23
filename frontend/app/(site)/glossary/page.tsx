import type { Metadata } from "next";
import { PagePlaceholder } from "@/components/layout/PagePlaceholder";
import { pages } from "@/lib/content/pages";

export const metadata: Metadata = { title: pages.glossary.name };

export default function GlossaryPage() {
  return <PagePlaceholder page={pages.glossary} />;
}
