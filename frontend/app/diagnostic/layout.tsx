import type { ReactNode } from "react";
import { FlowHeader } from "@/components/layout/FlowHeader";
import { pages } from "@/lib/content/pages";

export default function DiagnosticLayout({ children }: { children: ReactNode }) {
  return (
    <>
      <FlowHeader tag={pages.diagnostic.name} />
      <div className="flex-1">{children}</div>
    </>
  );
}
