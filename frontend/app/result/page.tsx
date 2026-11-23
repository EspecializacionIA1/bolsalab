import type { Metadata } from "next";
import { PagePlaceholder } from "@/components/layout/PagePlaceholder";
import { pages } from "@/lib/content/pages";

export const metadata: Metadata = { title: pages.result.name };

export default function ResultPage() {
  return <PagePlaceholder page={pages.result} />;
}
