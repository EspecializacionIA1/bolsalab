import type { Metadata } from "next";
import { PagePlaceholder } from "@/components/layout/PagePlaceholder";
import { pages } from "@/lib/content/pages";

export const metadata: Metadata = { title: pages.study.name };

export default function StudyPage() {
  return <PagePlaceholder page={pages.study} />;
}
