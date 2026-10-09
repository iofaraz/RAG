export default function Header() {
  return (
    <header className="border-b border-line/90 bg-[#fbfbf7]">
      <div className="mx-auto flex max-w-6xl items-center justify-between gap-4 px-4 py-4 sm:px-7 lg:px-10">
        <a href="#main-content" className="flex items-center gap-3 rounded-xl" aria-label="NutriVault home">
          <span className="grid size-11 place-items-center rounded-2xl bg-brand text-white shadow-sm shadow-brand/15">
            <svg viewBox="0 0 24 24" fill="none" className="size-6" aria-hidden="true">
              <path d="M19.8 4.5c-6.5-.4-11.2 1.1-13.5 4.4-1.7 2.5-.9 5.7 1.5 6.8 2.8 1.3 6.1-.7 7.8-3.3 1.6-2.5 2.8-5.4 4.2-7.9Z" fill="currentColor" opacity=".9" />
              <path d="M4.5 20c2.4-4.7 5.1-7.7 9-10" stroke="#D9EADD" strokeWidth="1.7" strokeLinecap="round" />
            </svg>
          </span>
          <span className="leading-tight">
            <span className="block text-lg font-semibold tracking-[-0.035em] text-ink">NutriVault</span>
            <span className="mt-0.5 block text-xs text-muted">Nutrition knowledge, grounded in data</span>
          </span>
        </a>

        <div className="hidden items-center gap-2 rounded-full border border-line bg-white px-3 py-2 text-xs font-medium text-muted sm:flex">
          <span className="size-2 rounded-full bg-accent" aria-hidden="true" />
          Evidence-led answers
        </div>
      </div>
    </header>
  );
}
