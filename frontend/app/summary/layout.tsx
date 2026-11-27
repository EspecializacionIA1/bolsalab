import type { ReactNode } from "react";
import { Footer } from "@/components/layout/Footer";
import { FlowHeader } from "@/components/layout/FlowHeader";
import { summaryCopy } from "@/lib/content/summary";

export default function SummaryLayout({ children }: { children: ReactNode }) {
  return (
    <>
      <FlowHeader tag={summaryCopy.name} />
      <div className="flex-1">{children}</div>
      <Footer />
    </>
  );
}
