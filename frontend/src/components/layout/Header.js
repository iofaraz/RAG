export default function Header() {
  return (
    <header className="border-b border-line bg-white">
      <div className="mx-auto flex max-w-3xl items-center gap-3 px-4 py-3 sm:px-6">
        {/* Placeholder mark — swap for a real logo asset later */}
        <span
          aria-hidden="true"
          className="grid size-8 place-items-center rounded-md bg-ink text-sm font-semibold text-white"
        >
          N
        </span>
        <div className="leading-tight">
          <p className="text-base font-semibold text-ink">Nutrivault</p>
          <p className="text-xs text-muted">AI Nutrition Knowledge</p>
        </div>
      </div>
    </header>
  );
}
