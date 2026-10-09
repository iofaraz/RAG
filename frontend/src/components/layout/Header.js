export default function Header() {
  return (
    <header className="border-b border-line/90 bg-[#fbfbf7]">
      <div className="mx-auto flex max-w-6xl items-center justify-between gap-4 px-4 py-4 sm:px-7 lg:px-10">
        <a
          href="#main-content"
          className="flex items-center gap-3 rounded-xl"
          aria-label="Nutrix home"
        >
          <span className="grid size-11 place-items-center rounded-2xl bg-brand text-white shadow-sm shadow-brand/15">
            <svg
              xmlns="http://www.w3.org/2000/svg"
              viewBox="0 0 512 512"
              width="100%"
              height="100%"
            >
              <defs>
                <linearGradient id="bgGrad" x1="0%" y1="0%" x2="100%" y2="100%">
                  <stop offset="0%" stop-color="#0f172a" />
                  <stop offset="100%" stop-color="#1e293b" />
                </linearGradient>

                <linearGradient
                  id="leafGrad"
                  x1="0%"
                  y1="0%"
                  x2="100%"
                  y2="100%"
                >
                  <stop offset="0%" stop-color="#4ade80" />
                  <stop offset="100%" stop-color="#16a34a" />
                </linearGradient>

                <linearGradient
                  id="dataGrad"
                  x1="0%"
                  y1="0%"
                  x2="100%"
                  y2="100%"
                >
                  <stop offset="0%" stop-color="#38bdf8" />
                  <stop offset="100%" stop-color="#0d9488" />
                </linearGradient>

                <filter id="glow" x="-20%" y="-20%" width="140%" height="140%">
                  <feGaussianBlur stdDeviation="6" result="blur" />
                  <feComposite in="SourceGraphic" in2="blur" operator="over" />
                </filter>
              </defs>

              <rect width="512" height="512" rx="112" fill="url(#bgGrad)" />

              <g
                stroke="url(#dataGrad)"
                stroke-width="4"
                opacity="0.4"
                stroke-dasharray="6,6"
              >
                <line x1="256" y1="230" x2="150" y2="150" />
                <line x1="256" y1="230" x2="362" y2="150" />
                <line x1="256" y1="230" x2="130" y2="330" />
                <line x1="256" y1="230" x2="382" y2="330" />
                <line x1="150" y1="150" x2="362" y2="150" />
              </g>

              <g fill="#38bdf8" filter="url(#glow)">
                <circle cx="150" cy="150" r="10" />
                <circle cx="362" cy="150" r="10" />
                <circle cx="130" cy="330" r="8" />
                <circle cx="382" cy="330" r="8" />
              </g>

              <path
                d="M 120 256 A 136 136 0 0 1 392 256"
                fill="none"
                stroke="url(#dataGrad)"
                stroke-width="6"
                stroke-linecap="round"
                stroke-dasharray="12 12"
              />

              <g transform="translate(0, 10)">
                <path
                  d="M 256 120 C 350 120 380 220 350 320 C 310 370 256 390 256 390 C 256 390 256 260 256 120 Z"
                  fill="url(#leafGrad)"
                />

                <path
                  d="M 256 120 C 162 120 132 220 162 320 C 202 370 256 390 256 390 C 256 390 256 260 256 120 Z"
                  fill="url(#leafGrad)"
                  opacity="0.8"
                />

                <path
                  d="M 256 390 L 256 200"
                  stroke="#ffffff"
                  stroke-width="8"
                  stroke-linecap="round"
                  opacity="0.9"
                />

                <path
                  d="M 256 310 L 295 280 M 256 270 L 305 235 M 256 230 L 285 200"
                  stroke="#ffffff"
                  stroke-width="5"
                  stroke-linecap="round"
                  opacity="0.8"
                />
                <path
                  d="M 256 290 L 220 265 M 256 250 L 210 220"
                  stroke="#ffffff"
                  stroke-width="5"
                  stroke-linecap="round"
                  opacity="0.8"
                />

                <circle
                  cx="256"
                  cy="200"
                  r="7"
                  fill="#ffffff"
                  filter="url(#glow)"
                />
                <circle cx="295" cy="280" r="5" fill="#ffffff" />
                <circle cx="305" cy="235" r="5" fill="#ffffff" />
                <circle cx="220" cy="265" r="5" fill="#ffffff" />
              </g>

              <path
                d="M 310 320 L 370 380"
                stroke="#4ade80"
                stroke-width="14"
                stroke-linecap="round"
                filter="url(#glow)"
              />
              <circle
                cx="290"
                cy="300"
                r="45"
                fill="none"
                stroke="#4ade80"
                stroke-width="8"
                opacity="0.9"
                filter="url(#glow)"
              />
            </svg>
          </span>
          <span className="leading-tight">
            <span className="block text-lg font-semibold tracking-[-0.035em] text-ink">
              Nutrix
            </span>
            <span className="mt-0.5 block text-xs text-muted">
              Nutrition knowledge, grounded in data
            </span>
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
