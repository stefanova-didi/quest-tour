import { afterEach, beforeEach, expect, it, vi } from "vitest";
import { api } from "./client";
import { makeState } from "../test/fixtures";

beforeEach(() => {
  vi.stubGlobal(
    "fetch",
    vi.fn(async () => ({
      ok: true,
      json: async () => ({ outcome: "ok", state: makeState() }),
    }))
  );
});

afterEach(() => {
  vi.unstubAllGlobals();
});

it("sends POST with an empty body for the compass action", async () => {
  await api.compass("my-token");
  expect(globalThis.fetch).toHaveBeenCalledOnce();
  const [, options] = vi.mocked(globalThis.fetch).mock.calls[0] as [
    string,
    RequestInit,
  ];
  expect(options.method).toBe("POST");
  expect(options.body).toBe("{}");
  expect(options.headers).toMatchObject({ "Content-Type": "application/json" });
});
