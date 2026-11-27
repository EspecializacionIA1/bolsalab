import { categoryColors } from "@/components/result/categoryColors";
import { Eyebrow } from "@/components/ui/Eyebrow";
import { tercileBar } from "@/lib/content/result";
import type { Result } from "@/schemas/prediction";

const order: Result["category"][] = ["less_likely", "similar", "more_likely"];

export function TercileBar({ category }: { category: Result["category"] }) {
  return (
    <div className="flex flex-col gap-3">
      <Eyebrow className="text-muted">{tercileBar.label}</Eyebrow>
      <ol className="grid grid-cols-3 gap-1.5">
        {order.map((item) => {
          const current = item === category;
          return (
            <li key={item} aria-current={current ? "true" : undefined} className="flex flex-col gap-2">
              <span className={`h-2 rounded-[1px] ${current ? `print-bar ${categoryColors[item].bar}` : "print-track bg-surface-raised"}`} />
              <span className={`text-sm ${current ? "font-medium text-foreground" : "text-muted"}`}>
                {tercileBar.segments[item]}
              </span>
              {current && (
                <span className={`font-mono text-[11px] tracking-[0.06em] uppercase ${categoryColors[item].text}`}>
                  {tercileBar.you}
                </span>
              )}
            </li>
          );
        })}
      </ol>
    </div>
  );
}
