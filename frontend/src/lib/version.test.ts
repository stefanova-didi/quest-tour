import { APP_VERSION, versionLabel } from "./version";

it("is baked in at build time", () => {
  expect(APP_VERSION).toMatch(/\S/);
});

it("labels tags, tag-relative builds, bare hashes and dev builds", () => {
  expect(versionLabel("v1.2.0")).toBe("v1.2.0");
  expect(versionLabel("v1.2.0-3-g6dd4e31")).toBe("v1.2.0-3-g6dd4e31");
  expect(versionLabel("1.2.0")).toBe("1.2.0");
  expect(versionLabel("6dd4e31")).toBe("build 6dd4e31");
  expect(versionLabel("6dd4e31-dirty")).toBe("build 6dd4e31-dirty");
  expect(versionLabel("dev")).toBe("development build");
});
