import { checklistCopy, checklistItems } from "@/lib/content/checklist";

export function BeforeInvesting() {
  return (
    <section aria-labelledby="before-investing-title" className="flex flex-col gap-4 border-t border-border pt-10">
      <h2 id="before-investing-title" className="text-2xl font-medium tracking-[-0.01em] md:text-3xl">
        {checklistCopy.title}
      </h2>
      <p className="text-muted">{checklistCopy.intro}</p>
      <div className="flex flex-col gap-2">
        {checklistItems.map((item) => (
          <details key={item.question} className="rounded-md border border-border bg-surface p-4">
            <summary className="cursor-pointer font-medium">{item.question}</summary>
            <div className="mt-3 flex flex-col gap-2 text-muted">
              <p>{item.how}</p>
              {item.links.map((link) => (
                <a
                  key={link.href}
                  href={link.href}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="w-fit text-primary underline underline-offset-4"
                >
                  {link.label} ↗
                </a>
              ))}
            </div>
          </details>
        ))}
      </div>
    </section>
  );
}
