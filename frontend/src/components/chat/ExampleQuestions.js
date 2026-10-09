import Button from "@/components/ui/Button";

const EXAMPLES = [
  "What foods are high in protein?",
  "Which foods are rich in calcium?",
  "Compare salmon and chicken.",
  "Which foods contain vitamin C?",
];

export default function ExampleQuestions({ onSelect, disabled }) {
  return (
    <section aria-labelledby="examples-heading" className="mt-7">
      <h2
        id="examples-heading"
        className="mb-3.5 text-xs font-semibold uppercase tracking-[0.12em] text-muted"
      >
        Try an example
      </h2>
      <ul className="flex flex-wrap gap-2.5">
        {EXAMPLES.map((example) => (
          <li key={example}>
            <Button
              variant="secondary"
              size="sm"
              disabled={disabled}
              onClick={() => onSelect(example)}
              className="h-auto min-h-[42px] w-full justify-start rounded-full border-line bg-white px-4 py-2.5 text-left text-sm font-medium text-brand shadow-[0_3px_12px_-9px_rgba(25,59,50,0.45)] transition-all hover:border-accent hover:bg-mint hover:text-ink sm:w-auto"
            >
              {example}
            </Button>
          </li>
        ))}
      </ul>
    </section>
  );
}
