import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import SectionLabel from "@/components/ui/SectionLabel";

const markdownComponents = {
  h1: ({ children }) => <h3 className="mb-3 mt-6 text-xl font-semibold tracking-tight text-ink first:mt-0">{children}</h3>,
  h2: ({ children }) => <h3 className="mb-3 mt-6 text-lg font-semibold tracking-tight text-ink first:mt-0">{children}</h3>,
  h3: ({ children }) => <h3 className="mb-2 mt-5 text-base font-semibold text-ink first:mt-0">{children}</h3>,
  p: ({ children }) => <p className="my-3 leading-7 text-slate-700 first:mt-0 last:mb-0">{children}</p>,
  ul: ({ children }) => <ul className="my-3 list-disc space-y-1.5 pl-6 marker:text-accent">{children}</ul>,
  ol: ({ children }) => <ol className="my-3 list-decimal space-y-1.5 pl-6 marker:font-semibold marker:text-brand">{children}</ol>,
  li: ({ children }) => <li className="pl-1 leading-7 text-slate-700">{children}</li>,
  strong: ({ children }) => <strong className="font-semibold text-ink">{children}</strong>,
  blockquote: ({ children }) => <blockquote className="my-4 border-l-2 border-accent pl-4 text-muted">{children}</blockquote>,
  table: ({ children }) => (
    <div className="my-5 overflow-x-auto rounded-xl border border-line">
      <table className="w-full min-w-[460px] border-collapse text-left text-sm">{children}</table>
    </div>
  ),
  thead: ({ children }) => <thead className="bg-mint text-ink">{children}</thead>,
  th: ({ children }) => <th className="whitespace-nowrap px-4 py-3 font-semibold">{children}</th>,
  td: ({ children }) => <td className="border-t border-line px-4 py-3 align-top text-slate-700">{children}</td>,
  hr: () => <hr className="my-5 border-line" />,
  a: ({ href, children }) => <a href={href} target="_blank" rel="noreferrer" className="font-medium text-brand underline decoration-accent/50 underline-offset-4 hover:text-accent-strong">{children}</a>,
};

export default function AIResponse({ answer, sourceCount }) {
  return (
    <article aria-label="Assistant answer" className="overflow-hidden rounded-2xl border border-line bg-white shadow-[0_12px_38px_-30px_rgba(25,59,50,0.4)]">
      <div className="flex flex-wrap items-center justify-between gap-3 border-b border-line bg-[#fbfcf8] px-5 py-4 sm:px-6">
        <div className="flex items-center gap-3">
          <span className="grid size-9 place-items-center rounded-xl bg-mint text-brand" aria-hidden="true">
            <svg viewBox="0 0 24 24" fill="none" className="size-5">
              <path d="M12 3.5 14.3 9l5.9.5-4.5 3.8 1.4 5.7-5.1-3.1-5.1 3.1 1.4-5.7-4.5-3.8 5.9-.5L12 3.5Z" fill="currentColor" />
            </svg>
          </span>
          <div>
            <SectionLabel>NutriVault answer</SectionLabel>
            <p className="mt-0.5 text-xs text-muted">AI-generated explanation</p>
          </div>
        </div>
        <span className="rounded-full border border-[#d9e8dc] bg-mint px-3 py-1.5 text-[11px] font-medium text-brand">
          {sourceCount} retrieved record{sourceCount === 1 ? "" : "s"}
        </span>
      </div>

      <div className="px-5 py-5 text-[15px] sm:px-6 sm:py-6">
        {answer ? (
          <ReactMarkdown remarkPlugins={[remarkGfm]} components={markdownComponents}>
            {answer}
          </ReactMarkdown>
        ) : (
          <p className="text-sm leading-6 text-muted">No answer was returned. Please try asking in a different way.</p>
        )}
      </div>
      <p className="border-t border-line px-5 py-3 text-xs leading-5 text-muted sm:px-6">
        Retrieved records are shown separately below and may not substantiate every statement in the explanation.
      </p>
    </article>
  );
}
