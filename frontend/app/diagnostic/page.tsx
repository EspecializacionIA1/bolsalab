import type { Metadata } from "next";
import { DiagnosticFlow } from "@/components/diagnostic/DiagnosticFlow";
import { pages } from "@/lib/content/pages";

export const metadata: Metadata = { title: pages.diagnostic.name };

export default function DiagnosticPage() {
  return <DiagnosticFlow />;
}
