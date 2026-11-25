"use client";

import { useState } from "react";
import { Eyebrow } from "@/components/ui/Eyebrow";
import { glossaryCopy, glossaryTerms } from "@/lib/content/glossary";
import { pages } from "@/lib/content/pages";

function normalize(text: string) {
  return text.normalize("NFD").replace(/[̀-ͯ]/g, "").toLowerCase();
}

export function GlossaryView() {
  const [query, setQuery] = useState("");

  const search = normalize(query.trim());
  const terms = glossaryTerms.filter(
    (item) => normalize(item.term).includes(search) || normalize(item.definition).includes(search),
  );

  return (
    <main className="mx-auto w-full max-w-[1312px] px-4 py-12 md:px-8 md:py-16">
      <div className="flex max-w-3xl flex-col gap-8">
        <div className="flex flex-col gap-3">
          <Eyebrow>{pages.glossary.name}</Eyebrow>
          <h1 className="text-4xl leading-tight font-medium tracking-[-0.02em] md:text-5xl">{pages.glossary.title}</h1>
          <p className="text-lg text-muted">{pages.glossary.description}</p>
        </div>

        <div className="flex flex-col gap-2">
          <label htmlFor="glossary-search" className="font-medium">
            {glossaryCopy.searchLabel}
          </label>
          <input
            id="glossary-search"
            type="search"
            value={query}
            placeholder={glossaryCopy.searchPlaceholder}
            onChange={(event) => setQuery(event.target.value)}
            className="h-12 rounded-md border border-border bg-surface px-4 text-base text-foreground placeholder:text-muted focus:border-primary"
          />
          <p aria-live="polite" className="text-sm text-muted">
            {glossaryCopy.count(terms.length, glossaryTerms.length)}
          </p>
        </div>

        {terms.length > 0 ? (
          <dl className="flex flex-col">
            {terms.map((item) => (
              <div key={item.term} className="flex flex-col gap-1 border-t border-border py-4">
                <dt className="text-lg font-medium">{item.term}</dt>
                <dd className="text-muted">{item.definition}</dd>
              </div>
            ))}
          </dl>
        ) : (
          <p className="text-muted">{glossaryCopy.empty}</p>
        )}
      </div>
    </main>
  );
}
