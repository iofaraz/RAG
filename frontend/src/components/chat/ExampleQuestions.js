import Button from "@/components/ui/Button";

const EXAMPLES = [
  "What foods are high in protein?",
  "Which foods are rich in calcium?",
  "Compare salmon and chicken.",
  "Which foods contain vitamin C?",
];

export default function ExampleQuestions({ onSelect, disabled }) {
  return (
    <section aria-labelledby="examples-heading" className="mt-6">
      <h2
        id="examples-heading"
        className="mb-3 text-[11px] font-semibold uppercase tracking-[0.12em] text-muted"
      >
        Try an example
      </h2>
      <ul className="grid gap-2 sm:grid-cols-2">
        {EXAMPLES.map((example) => (
          <li key={example}>
            <Button
              variant="secondary"
              size="sm"
              disabled={disabled}
              onClick={() => onSelect(example)}
              className="h-auto min-h-[42px] w-full justify-start rounded-md border border-line bg-white/80 px-3 py-2.5 text-left text-sm font-medium text-ink shadow-sm transition-all hover:border-brand/80 hover:bg-brand/5 hover:text-brand"
            >
              {example}
            </Button>
          </li>
        ))}
      </ul>
    </section>
  );
}
