import { useCallback, useState } from "react";

const STORAGE_KEY = "questtour-language";

export function getLanguage(): string {
  try {
    return localStorage.getItem(STORAGE_KEY) || "en";
  } catch {
    return "en";
  }
}

export function setLanguage(lang: string): void {
  try {
    localStorage.setItem(STORAGE_KEY, lang);
  } catch {
    // ignore private-mode errors
  }
}

export function useLanguage(): [string, (lang: string) => void] {
  const [lang, setLang] = useState(() => getLanguage());
  const change = useCallback((next: string) => {
    setLang(next);
    setLanguage(next);
  }, []);
  return [lang, change];
}
