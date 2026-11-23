type ProgressProps = {
  current: number;
  total: number;
  label: string;
};

function segmentColor(step: number, current: number) {
  if (step < current) return "bg-holds";
  if (step === current) return "bg-primary";
  return "bg-surface-raised";
}

export function Progress({ current, total, label }: ProgressProps) {
  const steps = Array.from({ length: total }, (_, index) => index + 1);

  return (
    <div
      role="progressbar"
      aria-label={label}
      aria-valuemin={1}
      aria-valuemax={total}
      aria-valuenow={current}
      className="flex gap-1"
    >
      {steps.map((step) => (
        <span key={step} className={`h-1.5 flex-1 rounded-[1px] ${segmentColor(step, current)}`} />
      ))}
    </div>
  );
}
