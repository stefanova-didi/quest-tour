export type I18nMap = Record<string, string> | undefined | null;

export function pickText(base: string, i18n: I18nMap, lang: string): string {
  if (!i18n) return base;
  const value = i18n[lang];
  if (!value || value.trim() === "") return base;
  return value;
}
