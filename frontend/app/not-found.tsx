import type { Metadata } from "next";
import { Footer } from "@/components/layout/Footer";
import { SiteHeader } from "@/components/layout/SiteHeader";
import { ButtonLink } from "@/components/ui/Button";
import { Eyebrow } from "@/components/ui/Eyebrow";
import { notFoundPage } from "@/lib/content/general";

export const metadata: Metadata = { title: notFoundPage.title };

export default function NotFound() {
  return (
    <>
      <SiteHeader />
      <main className="mx-auto flex w-full max-w-[1312px] flex-1 flex-col items-start gap-4 px-4 py-20 md:px-8">
        <Eyebrow>{notFoundPage.code}</Eyebrow>
        <h1 className="text-4xl leading-tight font-medium tracking-[-0.02em] md:text-5xl">
          {notFoundPage.title}
        </h1>
        <p className="max-w-xl text-lg text-muted">{notFoundPage.body}</p>
        <ButtonLink href="/" className="mt-2">
          {notFoundPage.cta}
        </ButtonLink>
      </main>
      <Footer />
    </>
  );
}
