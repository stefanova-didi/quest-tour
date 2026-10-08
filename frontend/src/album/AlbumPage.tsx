import { NotFoundScreen } from "../screens/NotFoundScreen";
import { AlbumScreen } from "./AlbumScreen";
import { MOCK_ALBUM, PREVIEW_TOKEN } from "./mock";

/** /album/{token}: the album a host shares with a team after the game. Design draft: only the preview
 *  token renders (with mock data); real albums arrive with the album API, which will resolve the token to
 *  the team's run and its photos. Until then any other token is "not found", never a different team's album. */
export function AlbumPage({ token }: { token: string }) {
  if (token === PREVIEW_TOKEN) return <AlbumScreen album={MOCK_ALBUM} />;
  return <NotFoundScreen title="Album not found" />;
}
