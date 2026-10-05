import { useEffect } from "react";
import { GameApp } from "./game/GameApp";
import { lastToken } from "./lib/storage";
import { NotFoundScreen } from "./screens/NotFoundScreen";

export function App({ path = window.location.pathname }: { path?: string }) {
  useEffect(() => {                          // belt-and-braces for copy paths CSS can't reach (Ctrl+A, long-press menus)
    const block = (e: Event) => {
      const target = e.target as HTMLElement | null;
      if (!target?.closest("input, textarea")) e.preventDefault();
    };
    for (const type of ["copy", "cut", "contextmenu", "selectstart"]) document.addEventListener(type, block);
    return () => { for (const type of ["copy", "cut", "contextmenu", "selectstart"]) document.removeEventListener(type, block); };
  }, []);
  const match = /^\/play\/([^/]+)$/.exec(path);
  if (match) {
    const token = safeDecode(match[1]);
    return token === null ? <NotFoundScreen /> : <GameApp token={token} />;
  }
  if (path === "/") return <Home />;
  return <NotFoundScreen />;
}

function safeDecode(segment: string): string | null {
  try { return decodeURIComponent(segment); } catch { return null; }   // bad %-escape in a truncated link
}

function Home() {
  const token = lastToken();
  useEffect(() => { if (token) window.location.replace(`/play/${encodeURIComponent(token)}`); }, [token]);
  return token ? null : <NotFoundScreen title="Open your game link" />;
}
