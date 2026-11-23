"use client";

import Link from "next/link";
import { useState } from "react";
import { Logo } from "@/components/layout/Logo";
import { Button, ButtonLink } from "@/components/ui/Button";
import { mainCta, menu, navLinks } from "@/lib/content/general";

export function SiteHeader() {
  const [open, setOpen] = useState(false);
  const close = () => setOpen(false);

  return (
    <header className="border-b border-border">
      <div className="mx-auto flex min-h-[86px] w-full max-w-[1312px] items-center justify-between gap-6 px-4 md:px-8">
        <Logo />

        <nav aria-label={menu.label} className="hidden items-center gap-7 lg:flex">
          {navLinks.map((link) => (
            <Link
              key={link.href}
              href={link.href}
              className="rounded-sm font-mono text-[13px] text-muted transition-colors hover:text-foreground"
            >
              {link.label}
            </Link>
          ))}
        </nav>

        <div className="hidden lg:block">
          <ButtonLink href={mainCta.href}>{mainCta.label}</ButtonLink>
        </div>

        <Button
          variant="ghost"
          className="lg:hidden"
          aria-expanded={open}
          aria-controls="mobile-menu"
          onClick={() => setOpen(!open)}
        >
          {open ? menu.close : menu.open}
        </Button>
      </div>

      {open && (
        <nav id="mobile-menu" aria-label={menu.label} className="border-t border-border lg:hidden">
          <div className="flex flex-col gap-1 px-4 py-4">
            {navLinks.map((link) => (
              <Link key={link.href} href={link.href} onClick={close} className="rounded-sm py-3 text-lg">
                {link.label}
              </Link>
            ))}
            <ButtonLink href={mainCta.href} onClick={close} className="mt-3">
              {mainCta.label}
            </ButtonLink>
          </div>
        </nav>
      )}
    </header>
  );
}
