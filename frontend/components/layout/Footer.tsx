import { footer } from "@/lib/content/general";

export function Footer() {
  return (
    <footer className="border-t border-border">
      <div className="mx-auto flex w-full max-w-[1312px] flex-col gap-4 px-4 py-8 md:px-8">
        <p className="max-w-3xl text-[13px] text-muted">{footer.legal}</p>
        <div className="flex flex-col gap-2 font-mono text-[11px] tracking-[0.06em] text-muted uppercase md:flex-row md:justify-between">
          <p>{footer.institution}</p>
          <p>{footer.disclaimer}</p>
        </div>
      </div>
    </footer>
  );
}
