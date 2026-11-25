import type { Metadata } from "next";
import { StudyView } from "@/components/study/StudyView";
import { pages } from "@/lib/content/pages";

export const metadata: Metadata = { title: pages.study.name };

export default function StudyPage() {
  return <StudyView />;
}
