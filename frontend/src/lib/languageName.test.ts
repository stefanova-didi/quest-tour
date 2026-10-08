import { languageName } from "./languageName";

it("names a language in that language", () => {
  expect(languageName("en")).toBe("English");
  expect(languageName("de")).toBe("Deutsch");
  expect(languageName("bg")).toBe("Български");
});

it("prefers the Latin script for Serbian, which is how the content is written", () => {
  expect(languageName("sr")).toBe("Srpski");
});

it("falls back to the upper-case code for anything it cannot name", () => {
  expect(languageName("xx")).toBe("XX");
  expect(languageName("not a tag")).toBe("NOT A TAG");
});
