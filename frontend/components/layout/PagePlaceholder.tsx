import { Eyebrow } from "@/components/ui/Eyebrow";
import { Notice } from "@/components/ui/Notice";
import { placeholder } from "@/lib/content/pages";

type PagePlaceholderProps = {
  page: { name: string; title: string; description: string };
};

export function PagePlaceholder({ page }: PagePlaceholderProps) {
  return (
    <main className="mx-auto flex w-full max-w-[1312px] flex-col gap-4 px-4 py-16 md:px-8">
      <Eyebrow>{page.name}</Eyebrow>
      <h1 className="max-w-3xl text-4xl leading-tight font-medium tracking-[-0.02em] md:text-5xl">
        {page.title}
      </h1>
      <p className="max-w-xl text-lg text-muted">{page.description}</p>
      <div className="mt-4 max-w-xl">
        <Notice>{placeholder}</Notice>
      </div>
    </main>
  );
}
