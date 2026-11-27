import { topBar } from "@/lib/content/general";

export function TopBar() {
  return (
    <div className="bg-surface font-mono print:hidden text-[11px] tracking-[0.06em] uppercase">
      <div className="mx-auto flex min-h-[33px] w-full max-w-[1312px] items-center justify-between gap-4 px-4 md:px-8">
        <p className="hidden items-center gap-2 text-holds sm:flex">
          <span className="size-1.5 rounded-full bg-holds" aria-hidden="true" />
          {topBar.status}
        </p>
        <p className="text-muted">{topBar.privacy}</p>
      </div>
    </div>
  );
}
