import { useCallback, useEffect, useState } from "react";
import { api, HttpError, LinkNotValidError } from "../api/client";
import type { LinkNotValidInfo } from "../api/types";
import { Icon } from "../components/Icon";
import { useLanguage } from "../lib/language";
import { LinkNotValidScreen } from "../screens/LinkNotValidScreen";
import { LoadingScreen } from "../screens/LoadingScreen";
import { NotFoundScreen } from "../screens/NotFoundScreen";
import { AlbumScreen } from "./AlbumScreen";
import { MOCK_ALBUM, PREVIEW_TOKEN } from "./mock";
import type { Album } from "./types";

type View =
  | { kind: "loading" }
  | { kind: "ready"; album: Album }
  | { kind: "not_ready" }          // 409: the run has not ended yet (R-10: no photos during the game)
  | { kind: "invalid"; info: LinkNotValidInfo }
  | { kind: "not_found" }
  | { kind: "error" };             // offline or a server error: offer a retry

/** /album/{token}: the memories album of a team link (issue #33). The same token as the game link, so
 *  the Finish screen links straight here; the API answers only once the run has ended. The preview
 *  token renders the mock album for design work. */
export function AlbumPage({ token }: { token: string }) {
  const [language, setLanguage] = useLanguage();
  const [view, setView] = useState<View>({ kind: "loading" });
  const preview = token === PREVIEW_TOKEN;

  const load = useCallback(async () => {
    setView({ kind: "loading" });
    try {
      setView({ kind: "ready", album: await api.album(token) });
    } catch (err) {
      if (err instanceof LinkNotValidError) setView({ kind: "invalid", info: err.info });
      else if (err instanceof HttpError && err.status === 409) setView({ kind: "not_ready" });
      else if (err instanceof HttpError && err.status < 500) setView({ kind: "not_found" });
      else setView({ kind: "error" });
    }
  }, [token]);

  useEffect(() => { if (!preview) void load(); }, [preview, load]);

  if (preview) return <AlbumScreen album={MOCK_ALBUM} language={language} onLanguageChange={setLanguage} />;
  switch (view.kind) {
    case "loading": return <LoadingScreen offline={false} />;
    case "ready": return <AlbumScreen album={view.album} language={language} onLanguageChange={setLanguage} />;
    case "invalid": return <LinkNotValidScreen info={view.info} />;
    case "not_found": return <NotFoundScreen title="Album not found" />;
    case "not_ready":
      return <AlbumNotice title="Your album isn't ready yet"
                          body="It is put together the moment your game ends. Finish the quest, then open this link again." />;
    case "error":
      return <AlbumNotice title="Couldn't load your album" body="Check your connection and try again." onRetry={load} />;
  }
}

function AlbumNotice({ title, body, onRetry }: { title: string; body: string; onRetry?: () => void }) {
  return (
    <div className="qs">
      <main className="qs-main qs-main--center">
        <div className="qs-sign qs-sign--gold"><Icon name="gallery" /></div>
        <div className="qs-center-copy">
          <h1 className="t-display-l">{title}</h1>
          <p className="t-body">{body}</p>
        </div>
        {onRetry && (
          <button type="button" className="qc-btn qc-btn--primary" onClick={onRetry}><Icon name="retry" />Try again</button>
        )}
      </main>
    </div>
  );
}
