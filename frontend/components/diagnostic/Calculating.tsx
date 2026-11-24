import { calculating } from "@/lib/content/diagnostic";

const dotDelays = ["[animation-delay:0ms]", "[animation-delay:200ms]", "[animation-delay:400ms]"];

export function Calculating() {
  return (
    <main className="mx-auto w-full max-w-[1312px] px-4 py-16 md:px-8 md:py-24">
      <div role="status" className="flex max-w-2xl flex-col gap-5">
        <span aria-hidden className="flex gap-2">
          {dotDelays.map((delay) => (
            <span key={delay} className={`size-2.5 rounded-full bg-primary motion-safe:animate-pulse ${delay}`} />
          ))}
        </span>
        <h1 className="text-3xl leading-[1.15] font-medium tracking-[-0.02em] md:text-[40px]">{calculating.title}</h1>
        <p className="text-lg text-muted">{calculating.body}</p>
      </div>
    </main>
  );
}
