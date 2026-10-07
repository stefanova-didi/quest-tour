import { renderHook, act } from "@testing-library/react";
import { beforeEach, expect, test } from "vitest";
import { getLanguage, setLanguage, useLanguage } from "./language";

beforeEach(() => {
  localStorage.clear();
});

test("getLanguage defaults to en when nothing is stored", () => {
  expect(getLanguage()).toBe("en");
});

test("setLanguage persists to localStorage", () => {
  setLanguage("de");
  expect(localStorage.getItem("questtour-language")).toBe("de");
});

test("useLanguage returns stored language and updates state", () => {
  localStorage.setItem("questtour-language", "sr");
  const { result } = renderHook(() => useLanguage());
  expect(result.current[0]).toBe("sr");

  act(() => {
    result.current[1]("de");
  });

  expect(result.current[0]).toBe("de");
  expect(localStorage.getItem("questtour-language")).toBe("de");
});
