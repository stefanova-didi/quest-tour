// Illustrations read the tokens, so a palette change (design/) recolours them with no edits here.
export function WelcomeSkyline() {
  return (
    <svg viewBox="0 0 358 64" width="358" height="64" aria-hidden="true" style={{ display: "block" }}>
      <path d="M0 64 V46 a14 14 0 0 1 28 0 V64 Z" fill="var(--patina-600)" />
      <rect x="40" y="22" width="26" height="42" fill="var(--patina-600)" />
      <path d="M40 22 a13 13 0 0 1 26 0 Z" fill="var(--patina-600)" />
      <rect x="51" y="2" width="4" height="10" fill="var(--gold-500)" />
      <path d="M78 64 V36 a28 28 0 0 1 56 0 V64 Z" fill="var(--gold-500)" />
      <rect x="104" y="0" width="4" height="10" fill="var(--gold-500)" />
      <rect x="146" y="26" width="76" height="38" fill="var(--theatre-500)" />
      <path d="M154 64 V52 a6 6 0 0 1 12 0 V64 Z" fill="var(--patina-800)" />
      <path d="M178 64 V52 a6 6 0 0 1 12 0 V64 Z" fill="var(--patina-800)" />
      <path d="M202 64 V52 a6 6 0 0 1 12 0 V64 Z" fill="var(--patina-800)" />
      <path d="M146 26 L184 12 L222 26 Z" fill="var(--theatre-500)" />
      <path d="M234 64 V44 a16 16 0 0 1 32 0 V64 Z" fill="var(--patina-300)" />
      <rect x="278" y="30" width="34" height="34" fill="var(--gold-300)" />
      <path d="M324 64 V40 a17 17 0 0 1 34 0 V64 Z" fill="var(--patina-600)" />
    </svg>
  );
}

export function Confetti() {
  return (
    <svg className="qs-confetti" viewBox="0 0 390 620" aria-hidden="true">
      <rect x="40" y="56" width="10" height="20" rx="2" fill="var(--gold-500)" transform="rotate(-24 45 66)" />
      <rect x="92" y="120" width="8" height="16" rx="2" fill="var(--patina-600)" transform="rotate(30 96 128)" />
      <circle cx="150" cy="60" r="5" fill="var(--theatre-500)" />
      <rect x="218" y="40" width="10" height="20" rx="2" fill="var(--patina-300)" transform="rotate(18 223 50)" />
      <rect x="300" y="78" width="10" height="20" rx="2" fill="var(--gold-500)" transform="rotate(40 305 88)" />
      <circle cx="344" cy="150" r="6" fill="var(--gold-300)" />
      <rect x="30" y="210" width="8" height="16" rx="2" fill="var(--theatre-500)" transform="rotate(-40 34 218)" />
      <circle cx="70" cy="300" r="5" fill="var(--gold-500)" />
      <rect x="336" y="250" width="8" height="16" rx="2" fill="var(--patina-600)" transform="rotate(-18 340 258)" />
      <rect x="352" y="360" width="10" height="20" rx="2" fill="var(--theatre-500)" transform="rotate(28 357 370)" />
      <circle cx="268" cy="140" r="4" fill="var(--patina-600)" />
      <rect x="120" y="22" width="8" height="14" rx="2" fill="var(--gold-300)" transform="rotate(50 124 29)" />
      <circle cx="28" cy="400" r="5" fill="var(--patina-300)" />
    </svg>
  );
}

export function CurtainArt() {
  return (
    <svg className="qs-curtain__art" viewBox="0 0 390 220" preserveAspectRatio="xMaxYMin slice" aria-hidden="true">
      <rect x="300" y="30" width="10" height="20" rx="2" fill="var(--gold-300)" transform="rotate(24 305 40)" />
      <circle cx="350" cy="70" r="6" fill="var(--patina-300)" />
      <rect x="250" y="16" width="8" height="16" rx="2" fill="var(--patina-300)" transform="rotate(-30 254 24)" />
      <circle cx="268" cy="96" r="4" fill="var(--gold-300)" />
      <rect x="356" y="128" width="10" height="20" rx="2" fill="var(--gold-500)" transform="rotate(-18 361 138)" />
      <circle cx="200" cy="30" r="4" fill="var(--gold-500)" />
      <path d="M310 220 V176 a26 26 0 0 1 52 0 V220 Z" fill="var(--patina-600)" />
      <path d="M250 220 V192 a16 16 0 0 1 32 0 V220 Z" fill="var(--patina-600)" />
    </svg>
  );
}

export function HourglassArt() {
  return (
    <svg className="qs-curtain__art" viewBox="0 0 390 220" preserveAspectRatio="xMaxYMin slice" aria-hidden="true">
      <path d="M310 220 V176 a26 26 0 0 1 52 0 V220 Z" fill="var(--patina-600)" />
      <path d="M250 220 V192 a16 16 0 0 1 32 0 V220 Z" fill="var(--patina-600)" />
      <path d="M300 40 h40 M300 104 h40 M304 40 c0 20 32 20 32 32 s-32 12 -32 32 M336 40 c0 20 -32 20 -32 32 s32 12 32 32"
            fill="none" stroke="var(--gold-300)" strokeWidth={4} strokeLinecap="round" />
    </svg>
  );
}

export function LoadingMark() {
  return (
    <svg viewBox="0 0 96 96" width="112" height="112" aria-hidden="true">
      <circle cx="48" cy="48" r="44" fill="none" stroke="var(--surface-sunken)" strokeWidth={6} />
      <g className="qs-spinner"><path d="M48 4 a44 44 0 0 1 44 44" fill="none" stroke="var(--patina-600)" strokeWidth={6} strokeLinecap="round" /></g>
      <path d="M28 70 V54 a20 20 0 0 1 40 0 V70 Z" fill="var(--gold-500)" />
      <rect x="46" y="22" width="4" height="12" fill="var(--gold-700)" />
      <rect x="42" y="26" width="12" height="3" fill="var(--gold-700)" />
      <rect x="24" y="70" width="48" height="6" rx="2" fill="var(--patina-600)" />
    </svg>
  );
}
