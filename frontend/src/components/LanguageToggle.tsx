import { useEffect, useId, useMemo, useRef, useState } from "react";
import { languageName } from "../lib/languageName";
import { Icon } from "./Icon";

const BASE = "en";

/** The language control (issue #6): a small pill in the top band of every screen with translatable
 *  content – the in-game header, the cover and the welcome hero – that opens a bottom sheet listing
 *  the game's languages by their own names. A sheet rather than a dropdown: the bands clip overflow,
 *  the cover's text sits at the bottom of the screen, and a sheet is what a thumb expects on a phone.
 *  Renders nothing when the game has no translations, so an English-only game shows no control. */
export function LanguageToggle({ languages, selected, onSelect }: {
  languages: string[];
  selected: string;
  onSelect(lang: string): void;
}) {
  const all = useMemo(() => [BASE, ...languages.filter((code) => code !== BASE)], [languages]);
  const [open, setOpen] = useState(false);
  const triggerRef = useRef<HTMLButtonElement>(null);
  const titleId = useId();

  if (languages.length === 0) return null;

  const close = () => {
    setOpen(false);
    triggerRef.current?.focus();
  };
  const choose = (code: string) => {
    onSelect(code);
    close();
  };

  return (
    <>
      <button
        ref={triggerRef}
        type="button"
        className="qc-lang"
        aria-haspopup="dialog"
        aria-expanded={open}
        aria-label={`Language, ${selected.toUpperCase()}`}
        onClick={() => setOpen(true)}
      >
        <Icon name="globe" size={18} />
        <span>{selected.toUpperCase()}</span>
      </button>
      {open && (
        <LanguageSheet all={all} selected={selected} titleId={titleId} onChoose={choose} onClose={close} />
      )}
    </>
  );
}

function LanguageSheet({ all, selected, titleId, onChoose, onClose }: {
  all: string[]; selected: string; titleId: string; onChoose(code: string): void; onClose(): void;
}) {
  const selectedRef = useRef<HTMLButtonElement>(null);
  useEffect(() => { selectedRef.current?.focus(); }, []);
  useEffect(() => {
    const onKey = (e: KeyboardEvent) => { if (e.key === "Escape") onClose(); };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [onClose]);

  return (
    <div className="qs-overlay qc-scrim qc-lang-scrim" onClick={(e) => { if (e.target === e.currentTarget) onClose(); }}>
      <div className="qc-sheet qc-lang-sheet" role="dialog" aria-modal="true" aria-labelledby={titleId}>
        <h2 className="qc-sheet__title" id={titleId}>Language</h2>
        <div className="qc-lang-list" role="listbox" aria-labelledby={titleId}>
          {all.map((code) => {
            const current = code === selected;
            return (
              <button
                key={code}
                ref={current ? selectedRef : undefined}
                type="button"
                role="option"
                aria-selected={current}
                className="qc-lang-option"
                onClick={() => onChoose(code)}
              >
                <span className="qc-lang-option__code" aria-hidden="true">{code.toUpperCase()}</span>
                <span className="qc-lang-option__name">{languageName(code)}</span>
                {current && <Icon name="check" size={20} />}
              </button>
            );
          })}
        </div>
      </div>
    </div>
  );
}
