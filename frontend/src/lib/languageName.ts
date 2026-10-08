/** Native display name of a language code for the language sheet ("Deutsch", not "DE"), from the
 *  browser's own locale data so a new language in the YAML needs no code change. The code itself is
 *  the fallback for anything the browser cannot name. */

// The Serbian content is written in the Latin script; Intl would offer the Cyrillic "српски".
const OVERRIDES: Record<string, string> = { sr: "Srpski" };

export function languageName(code: string): string {
  const lower = code.toLowerCase();
  const override = OVERRIDES[lower];
  if (override) return override;
  try {
    const name = new Intl.DisplayNames([code], { type: "language" }).of(code);
    if (name && name.toLowerCase() !== lower) {
      return name.charAt(0).toLocaleUpperCase(code) + name.slice(1);
    }
  } catch {
    // malformed code, or a runtime without Intl.DisplayNames: fall through to the code
  }
  return code.toUpperCase();
}
