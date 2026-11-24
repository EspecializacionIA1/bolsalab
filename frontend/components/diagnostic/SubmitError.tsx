import { Button } from "@/components/ui/Button";
import { Notice } from "@/components/ui/Notice";
import { submitErrors } from "@/lib/content/diagnostic";
import type { ApiErrorKind } from "@/services/api-client";

type SubmitErrorProps = {
  kind: ApiErrorKind;
  onAction: () => void;
};

export function SubmitError({ kind, onAction }: SubmitErrorProps) {
  const error = submitErrors[kind];

  return (
    <div role="alert">
      <Notice title={error.title} tone="error">
        <div className="flex flex-col items-start gap-3">
          <p>{error.body}</p>
          <Button variant="ghost" onClick={onAction}>
            {error.action}
          </Button>
        </div>
      </Notice>
    </div>
  );
}
