export default function EmptyState() {
  return (
    <section className="relative isolate overflow-hidden rounded-[2rem] border border-[#dce6dc] bg-[#eaf1e8] px-6 py-9 sm:px-10 sm:py-12 lg:px-14 lg:py-14">
      <div className="absolute -right-10 -top-16 -z-10 size-64 rounded-full bg-white/45 blur-2xl" aria-hidden="true" />
      <div className="absolute bottom-0 right-10 -z-10 hidden size-36 rounded-full border border-white/60 sm:block" aria-hidden="true" />
      <div className="max-w-2xl">
        <span className="inline-flex items-center gap-2 rounded-full border border-[#d4e3d5] bg-white/70 px-3 py-1.5 text-xs font-semibold tracking-wide text-brand">
          <svg viewBox="0 0 20 20" fill="none" className="size-4" aria-hidden="true">
            <path d="M16.4 3.8c-5.4-.3-9.3.9-11.2 3.7-1.4 2.1-.8 4.7 1.3 5.7 2.3 1.1 5.1-.6 6.5-2.8 1.3-2.1 2.3-4.5 3.4-6.6Z" fill="currentColor" />
            <path d="M3.6 16.7c2-3.9 4.2-6.4 7.5-8.3" stroke="#EAF1E8" strokeWidth="1.5" strokeLinecap="round" />
          </svg>
          YOUR NUTRITION RESEARCH COMPANION
        </span>
        <h1 className="mt-5 max-w-xl text-4xl font-semibold leading-[1.08] tracking-[-0.05em] text-ink sm:text-5xl">
          Make sense of what&apos;s on your plate.
        </h1>
        <p className="mt-4 max-w-xl text-base leading-7 text-[#52685c] sm:text-lg sm:leading-8">
          Ask about foods and nutrients. Nutrix brings together an AI explanation and the nutrition records retrieved for your question.
        </p>
        <div className="mt-7 flex flex-wrap gap-x-5 gap-y-2 text-xs font-medium text-brand sm:text-sm">
          <span className="inline-flex items-center gap-2"><span className="size-1.5 rounded-full bg-accent" />Grounded in retrieved data</span>
          <span className="inline-flex items-center gap-2"><span className="size-1.5 rounded-full bg-accent" />Clear supporting records</span>
        </div>
      </div>
    </section>
  );
}
