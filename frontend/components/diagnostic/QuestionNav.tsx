import { Button } from "@/components/ui/Button";
import { navigation } from "@/lib/content/diagnostic";

type QuestionNavProps = {
  showBack: boolean;
  isLast: boolean;
  canContinue: boolean;
  onBack: () => void;
  onNext: () => void;
};

export function QuestionNav({ showBack, isLast, canContinue, onBack, onNext }: QuestionNavProps) {
  return (
    <div className="flex items-center justify-between gap-3 border-t border-border pt-6">
      {showBack ? (
        <Button variant="ghost" onClick={onBack}>
          ← {navigation.back}
        </Button>
      ) : (
        <span />
      )}
      <Button disabled={!canContinue} onClick={onNext}>
        {isLast ? navigation.finish : `${navigation.next} →`}
      </Button>
    </div>
  );
}
