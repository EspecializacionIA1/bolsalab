import { Logo } from "@/components/layout/Logo";

export function FlowHeader({ tag }: { tag: string }) {
  return (
    <header className="border-b border-border">
      <div className="mx-auto flex min-h-[86px] w-full max-w-[1312px] items-center px-4 md:px-8">
        <Logo tag={tag} />
      </div>
    </header>
  );
}
