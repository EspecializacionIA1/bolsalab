import type { Metadata } from "next";
import { PagePlaceholder } from "@/components/layout/PagePlaceholder";
import { pages } from "@/lib/content/pages";

export const metadata: Metadata = { title: pages.simulator.name };

export default function SimulatorPage() {
  return <PagePlaceholder page={pages.simulator} />;
}
