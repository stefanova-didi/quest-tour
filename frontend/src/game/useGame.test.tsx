import { act, renderHook } from "@testing-library/react";
import { afterEach, beforeEach, expect, it, vi } from "vitest";
import { api, HttpError, LinkNotValidError, NetworkError } from "../api/client";
import type { ActionResult, LinkNotValidInfo } from "../api/types";
import { makeState, makeTask } from "../test/fixtures";
import { POLL_MS, RETRY_MS, useGame } from "./useGame";

vi.mock("../api/client", async (importOriginal) => ({
  ...(await importOriginal<typeof import("../api/client")>()),
  api: { state: vi.fn(), answer: vi.fn(), compass: vi.fn() },
}));

const getState = vi.mocked(api.state);
const flush = (ms = 0) => act(async () => { await vi.advanceTimersByTimeAsync(ms); });

function deferred<T>() {
  let resolve!: (value: T) => void;
  const promise = new Promise<T>((r) => { resolve = r; });
  return { promise, resolve };
}

function mount(token = "tok") {
  const hook = renderHook(() => useGame(token));
  const version = () => (hook.result.current.view.kind === "ready" ? hook.result.current.view.state.version : null);
  return { ...hook, version };
}

beforeEach(() => {
  vi.useFakeTimers();
  getState.mockReset();
  vi.spyOn(console, "error").mockImplementation(() => {});
  Object.defineProperty(document, "visibilityState", { value: "visible", configurable: true });
});
afterEach(() => {
  vi.useRealTimers();
  vi.restoreAllMocks();
});

it("loads, polls every 60 s and refreshes when the page becomes visible", async () => {
  getState.mockResolvedValue(makeState({ version: 3 }));
  const { result } = mount();
  await flush();
  expect(result.current.view.kind).toBe("ready");
  expect(getState).toHaveBeenCalledTimes(1);
  await flush(POLL_MS);
  expect(getState).toHaveBeenCalledTimes(2);
  await act(async () => { document.dispatchEvent(new Event("visibilitychange")); });
  await flush();
  expect(getState).toHaveBeenCalledTimes(3);
});

it("shows the offline banner on network errors, retries after 5 s, and ignores a 422", async () => {
  getState.mockRejectedValueOnce(new NetworkError()).mockResolvedValue(makeState());
  const { result } = mount();
  await flush();
  expect(result.current.offline).toBe(true);
  await flush(RETRY_MS);
  expect(getState).toHaveBeenCalledTimes(2);
  expect(result.current.offline).toBe(false);
  expect(result.current.view.kind).toBe("ready");
  getState.mockRejectedValueOnce(new HttpError(422));
  await act(async () => { await result.current.refresh(); });
  expect(result.current.offline).toBe(false);
  expect(result.current.view.kind).toBe("ready");          // a later 4xx never replaces a shown game
});

it("shows Link not valid for a 403, and for an unexpected 4xx on the first load", async () => {
  const info: LinkNotValidInfo = { code: "link_not_valid", reason: "expired", opens_at: null,
                                   expired_at: "2026-09-14T21:00:00+00:00", time_zone: "Europe/Sofia" };
  getState.mockRejectedValueOnce(new LinkNotValidError(info));
  const first = mount();
  await flush();
  expect(first.result.current.view).toEqual({ kind: "invalid", info });
  first.unmount();

  getState.mockRejectedValueOnce(new HttpError(404));
  const second = mount("a/b");
  await flush();
  expect(second.result.current.view.kind).toBe("invalid");
});

it("orders states by server version, not by arrival, and raises no toast for its own action", async () => {
  getState.mockResolvedValueOnce(makeState({ version: 3 }));
  const { result, version } = mount();
  await flush();
  const own = deferred<ActionResult>();
  let pending!: Promise<unknown>;
  await act(async () => { pending = result.current.act(() => own.promise); });

  getState.mockResolvedValueOnce(makeState({ version: 4, phase: "photo" }));   // poll served after the answer
  await act(async () => { await result.current.refresh(); });
  expect(version()).toBe(4);
  expect(result.current.notice).toBeNull();                                    // own action in flight

  await act(async () => {
    own.resolve({ outcome: "correct", state: makeState({ version: 5, phase: "photo" }) });
    await pending;
  });
  expect(version()).toBe(5);

  getState.mockResolvedValueOnce(makeState({ version: 4, phase: "photo" }));   // a slow, older poll
  await act(async () => { await result.current.refresh(); });
  expect(version()).toBe(5);
  expect(result.current.notice).toBeNull();
});

it("raises a teammate notice for a change made on another phone", async () => {
  getState.mockResolvedValueOnce(makeState({ version: 3 }))
          .mockResolvedValueOnce(makeState({ version: 4, phase: "photo" }));
  const { result } = mount();
  await flush();
  await flush(POLL_MS);
  expect(result.current.notice).toBe("A teammate solved this task");
});

it("raises a teammate notice when a teammate opens the compass", async () => {
  const closed = makeTask({ compass: { opened: false, lat: 42.7, lon: 23.3, penalty_minutes: 5 } });
  const opened = makeTask({ compass: { opened: true, lat: 42.7, lon: 23.3, penalty_minutes: 5 } });
  getState.mockResolvedValueOnce(makeState({ version: 3, task: closed }))
          .mockResolvedValueOnce(makeState({ version: 4, task: opened }));
  const { result } = mount();
  await flush();
  await flush(POLL_MS);
  expect(result.current.notice).toBe("A teammate opened the compass");
});

it("does not blame a teammate when its own action's response was lost", async () => {
  getState.mockResolvedValueOnce(makeState({ version: 3 }));
  const { result, version } = mount();
  await flush();
  await act(async () => { await result.current.act(() => Promise.reject(new NetworkError())); });
  expect(result.current.offline).toBe(true);
  getState.mockResolvedValueOnce(makeState({ version: 4, phase: "photo" }));   // the answer did land
  await flush(RETRY_MS);
  expect(version()).toBe(4);
  expect(result.current.notice).toBeNull();
});

it("accepts the not-started state after a reset because its version is higher", async () => {
  getState.mockResolvedValueOnce(makeState({ version: 12, service: true }))
          .mockResolvedValueOnce(makeState({ version: 13, service: true, status: "not_started", phase: null,
                                             position: 0, clock: null, task: null }));
  const { result } = mount();
  await flush();
  await flush(POLL_MS);
  const view = result.current.view;
  expect(view.kind === "ready" && view.state.status).toBe("not_started");
});
