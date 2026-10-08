/** The version of this build, from `git describe` or the APP_VERSION build variable (vite.config.ts):
 *  a release tag such as `v1.2.0`, `v1.2.0-3-g6dd4e31` for a build three commits past the tag, a bare
 *  commit hash when nothing is tagged yet, or `dev`. The backend reports the same string in
 *  GET /api/health, so the footer and the health check together say which version is running. */
export const APP_VERSION: string =
  typeof __APP_VERSION__ === "string" && __APP_VERSION__ !== "" ? __APP_VERSION__ : "dev";

/** Footer label for a version string: tags and tag-relative builds read as they are; a bare commit
 *  hash is called a build so it is not mistaken for a release. */
export function versionLabel(version: string = APP_VERSION): string {
  if (version === "dev") return "development build";
  // A tag is v1.2.0 (or 1.2.0); a bare hash such as 6dd4e31 can start with a digit but has no dot.
  return /^v?\d+\.\d+/.test(version) ? version : `build ${version}`;
}
