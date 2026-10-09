import SectionLabel from "@/components/ui/SectionLabel";

export default function UserQuestion({ question }) {
  return (
    <section aria-label="Your question" className="flex items-start gap-3 sm:gap-4">
      <span className="grid size-9 shrink-0 place-items-center rounded-xl border border-line bg-white text-brand" aria-hidden="true">
        <svg viewBox="0 0 20 20" fill="none" className="size-4">
          <path d="M4 5.5h12M4 10h8M4 14.5h5" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" />
        </svg>
      </span>
      <div className="min-w-0 pt-0.5">
        <SectionLabel>Your question</SectionLabel>
        <p className="mt-1.5 break-words text-lg font-semibold leading-snug tracking-tight text-ink sm:text-xl">{question}</p>
      </div>
    </section>
  );
}
