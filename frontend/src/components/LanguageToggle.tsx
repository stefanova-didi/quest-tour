import { useMemo } from "react";

export function LanguageToggle({ languages, selected, onSelect, compact = false }: {
  languages: string[];
  selected: string;
  onSelect(lang: string): void;
  compact?: boolean;
}) {
  const all = useMemo(() => ["en", ...languages], [languages]);
  const label = (code: string) => code === "en" ? "Base / EN" : code.toUpperCase();

  return (
    <div className={`qc-lang-toggle ${compact ? "qc-lang-toggle--compact" : ""}`} role="group" aria-label="Language">
      {all.map((code) => (
        <button
          key={code}
          type="button"
          className={`qc-btn ${selected === code ? "qc-btn--primary" : "qc-btn--secondary"}`}
          aria-pressed={selected === code}
          onClick={() => onSelect(code)}
        >
          {label(code)}
        </button>
      ))}
    </div>
  );
}
