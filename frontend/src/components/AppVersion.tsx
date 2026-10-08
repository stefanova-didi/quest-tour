import { APP_VERSION, versionLabel } from "../lib/version";

/** App footer: the version of the running build (issue #29), so a tester and the host can tell which
 *  release a phone or the admin panel is on. `inverse` is for the dark patina bands. */
export function AppVersion({ inverse = false }: { inverse?: boolean }) {
  return (
    <footer className={inverse ? "qs-version qs-version--inverse" : "qs-version"}>
      <span>Quest City Tour</span>
      <span className="qs-version__value" data-testid="app-version">{versionLabel(APP_VERSION)}</span>
    </footer>
  );
}
