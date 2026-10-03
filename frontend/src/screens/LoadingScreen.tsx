import { ConnectionBanner } from "../components/ConnectionBanner";
import { LoadingMark } from "../components/art";

export function LoadingScreen({ offline }: { offline: boolean }) {
  return (
    <div className="qs">
      {offline && <ConnectionBanner />}
      <main className="qs-main qs-main--center" style={{ gap: 24 }} role="status">
        <LoadingMark />
        <div style={{ display: "grid", gap: 8 }}>
          <p className="t-title">Loading your quest…</p>
          <p className="t-caption">On a weak signal this can take a few seconds.</p>
        </div>
      </main>
    </div>
  );
}
