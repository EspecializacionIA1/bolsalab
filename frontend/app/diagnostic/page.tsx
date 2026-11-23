import type { Metadata } from "next";
import { PagePlaceholder } from "@/components/layout/PagePlaceholder";
import { pages } from "@/lib/content/pages";

export const metadata: Metadata = { title: pages.diagnostic.name };

export default function DiagnosticPage() {
  return <PagePlaceholder page={pages.diagnostic} />;
}
