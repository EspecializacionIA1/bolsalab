type OptionProps = {
  name: string;
  letter: string;
  label: string;
  checked: boolean;
  onSelect: () => void;
};

export function Option({ name, letter, label, checked, onSelect }: OptionProps) {
  const box = checked ? "border-primary bg-primary/10" : "border-border bg-surface hover:border-muted";
  const mark = checked ? "border-primary bg-primary text-on-primary" : "border-border text-muted";

  return (
    <label
      className={`flex min-h-[75px] cursor-pointer items-center gap-4 rounded-md border px-5 py-3 text-lg transition-colors has-focus-visible:outline-2 has-focus-visible:outline-offset-2 has-focus-visible:outline-primary ${box}`}
    >
      <input type="radio" name={name} checked={checked} onChange={onSelect} className="sr-only" />
      <span className={`flex size-8 shrink-0 items-center justify-center rounded-sm border font-mono text-sm ${mark}`}>
        {letter}
      </span>
      {label}
    </label>
  );
}
