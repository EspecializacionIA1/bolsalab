import type { ReactNode } from "react";
import { Footer } from "@/components/layout/Footer";
import { FlowHeader } from "@/components/layout/FlowHeader";
import { pages } from "@/lib/content/pages";

export default function ResultLayout({ children }: { children: ReactNode }) {
  return (
    <>
      <FlowHeader tag={pages.result.name} />
      <div className="flex-1">{children}</div>
      <Footer />
    </>
  );
}
