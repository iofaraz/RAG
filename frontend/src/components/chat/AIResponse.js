import SectionLabel from "@/components/ui/SectionLabel";

export default function AIResponse({ answer, sourceCount }) {
  const paragraphs = answer.split(/\n{2,}/).filter(Boolean);

  return (
    <article className="rounded-lg border border-line border-l-4 border-l-accent bg-white p-5 sm:p-6">
      <SectionLabel>AI answer</SectionLabel>
      <div className="mt-3 space-y-3 text-[15px] leading-7 text-slate-800">
        {paragraphs.map((paragraph, index) => (
          <p key={index}>{paragraph}</p>
        ))}
      </div>
      <p className="mt-4 border-t border-line pt-3 text-xs text-muted">
        Generated from {sourceCount} retrieved nutrition record
        {sourceCount === 1 ? "" : "s"} listed below.
      </p>
    </article>
  );
}
