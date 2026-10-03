import { beforeEach, describe, expect, it, vi } from "vitest";
import { forgetToken, getDeviceId, lastToken, rememberToken } from "./storage";

describe("storage", () => {
  beforeEach(() => {
    localStorage.clear();
    vi.restoreAllMocks();
  });

  it("keeps one device id per browser", () => {
    const id = getDeviceId();
    expect(id).toBeTruthy();
    expect(getDeviceId()).toBe(id);
  });

  it("remembers and forgets the last token", () => {
    expect(lastToken()).toBeNull();
    rememberToken("abc");
    expect(lastToken()).toBe("abc");
    forgetToken("other");
    expect(lastToken()).toBe("abc");
    forgetToken("abc");
    expect(lastToken()).toBeNull();
  });

  it("survives blocked storage", () => {
    vi.spyOn(Storage.prototype, "getItem").mockImplementation(() => { throw new Error("blocked"); });
    vi.spyOn(Storage.prototype, "setItem").mockImplementation(() => { throw new Error("blocked"); });
    expect(lastToken()).toBeNull();
    expect(() => rememberToken("abc")).not.toThrow();
    expect(() => forgetToken("abc")).not.toThrow();
    const id = getDeviceId();
    expect(getDeviceId()).toBe(id);
  });
});
