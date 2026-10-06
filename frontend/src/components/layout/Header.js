export default function Header() {
  return (
    <header className="border-b border-line bg-white/90 backdrop-blur-sm">
      <div className="mx-auto flex max-w-3xl items-center gap-3 px-4 py-3 sm:px-6">
        <span
          aria-hidden="true"
          className="grid size-8 place-items-center rounded-full bg-ink text-sm font-semibold text-white shadow-sm ring-2 ring-white"
        >
          N
        </span>
        <div className="leading-tight">
          <p className="text-base font-semibold tracking-tight text-ink">Nutrivault</p>
          <p className="text-xs text-muted">AI Nutrition Knowledge</p>
        </div>
      </div>
    </header>
  );
}
