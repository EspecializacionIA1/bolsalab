import type { Metadata } from "next";
import { PagePlaceholder } from "@/components/layout/PagePlaceholder";
import { pages } from "@/lib/content/pages";

export const metadata: Metadata = { title: pages.plan.name };

export default function PlanPage() {
  return <PagePlaceholder page={pages.plan} />;
}
