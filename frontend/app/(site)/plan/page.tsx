import type { Metadata } from "next";
import { PlanView } from "@/components/plan/PlanView";
import { pages } from "@/lib/content/pages";

export const metadata: Metadata = { title: pages.plan.name };

export default function PlanPage() {
  return <PlanView />;
}
