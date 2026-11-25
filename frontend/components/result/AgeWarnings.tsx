import { Notice } from "@/components/ui/Notice";
import { ageWarnings } from "@/lib/content/result";

const SENIOR_AGE = 60;

type AgeWarningsProps = {
  age?: number;
  warnings: string[];
};

export function ageMessages(age: number | undefined, warnings: string[]): string[] {
  const messages: string[] = [];
  if (warnings.includes("age_outside_training_range")) messages.push(ageWarnings.outsideRange);
  if (age !== undefined && age >= SENIOR_AGE) messages.push(ageWarnings.senior);
  return messages;
}

export function AgeWarnings({ age, warnings }: AgeWarningsProps) {
  const messages = ageMessages(age, warnings);

  if (messages.length === 0) return null;

  return (
    <div className="flex flex-col gap-3">
      {messages.map((message) => (
        <Notice key={message} tone="warning">
          {message}
        </Notice>
      ))}
    </div>
  );
}
