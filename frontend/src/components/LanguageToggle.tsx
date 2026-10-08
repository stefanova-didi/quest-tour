import { useEffect, useMemo, useRef, useState } from "react";
import { Icon } from "./Icon";

const BASE = "en";
const label = (code: string) => code.toUpperCase();

export function LanguageToggle({ languages, selected, onSelect, compact = false }: {
  languages: string[];
  selected: string;
  onSelect(lang: string): void;
  compact?: boolean;
}) {
  const all = useMemo(() => [BASE, ...languages], [languages]);
  const [open, setOpen] = useState(false);
  const rootRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!open) return;
    const onPointerDown = (event: PointerEvent) => {
      if (!rootRef.current?.contains(event.target as Node)) setOpen(false);
    };
    const onKeyDown = (event: KeyboardEvent) => {
      if (event.key === "Escape") setOpen(false);
    };
    document.addEventListener("pointerdown", onPointerDown);
    document.addEventListener("keydown", onKeyDown);
    return () => {
      document.removeEventListener("pointerdown", onPointerDown);
      document.removeEventListener("keydown", onKeyDown);
    };
  }, [open]);

  return (
    <div className={`qc-lang ${compact ? "qc-lang--compact" : ""}`} ref={rootRef}>
      <button
        type="button"
        className="qc-btn qc-btn--secondary qc-lang__trigger"
        aria-haspopup="listbox"
        aria-expanded={open}
        aria-label={`Language, ${label(selected)}`}
        onClick={() => setOpen((value) => !value)}
      >
        {label(selected)}
        <svg viewBox="0 0 16 16" aria-hidden="true"><path d="M4 6l4 4 4-4" fill="none" stroke="currentColor" strokeWidth={2} strokeLinecap="round" strokeLinejoin="round" /></svg>
      </button>
      {open && (
        <ul className="qc-lang__menu" role="listbox" aria-label="Language">
          {all.map((code) => (
            <li
              key={code}
              role="option"
              aria-selected={selected === code}
              onClick={() => { onSelect(code); setOpen(false); }}
            >
              {label(code)}
              {selected === code && <Icon name="check" size={16} />}
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
