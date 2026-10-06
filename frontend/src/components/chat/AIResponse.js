import SectionLabel from "@/components/ui/SectionLabel";

export default function AIResponse({ answer, sourceCount }) {
  const paragraphs = answer.split(/\n{2,}/).filter(Boolean);

  return (
    <article className="rounded-xl border border-line bg-white p-5 shadow-sm sm:p-6">
      <div className="flex items-center justify-between gap-3">
        <SectionLabel>AI answer</SectionLabel>
        <span className="rounded-full border border-brand/15 bg-brand/5 px-2 py-1 text-[10px] font-medium uppercase tracking-[0.12em] text-brand">
          Grounded in retrieved nutrition data
        </span>
      </div>
      <div className="mt-4 space-y-3 text-[15px] leading-7 text-slate-800">
        {paragraphs.map((paragraph, index) => (
          <p key={index}>{paragraph}</p>
        ))}
      </div>
      <p className="mt-4 border-t border-line pt-3 text-xs text-muted">
        Based on {sourceCount} retrieved nutrition source
        {sourceCount === 1 ? "" : "s"}.
      </p>
    </article>
  );
}
