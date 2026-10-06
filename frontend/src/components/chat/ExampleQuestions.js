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
      <h2 id="examples-heading" className="mb-3 text-xs font-semibold uppercase tracking-wider text-muted">
        Try an example
      </h2>
      <ul className="flex flex-wrap gap-2">
        {EXAMPLES.map((example) => (
          <li key={example}>
            <Button
              variant="secondary"
              size="sm"
              disabled={disabled}
              onClick={() => onSelect(example)}
              className="text-left"
            >
              {example}
            </Button>
          </li>
        ))}
      </ul>
    </section>
  );
}
