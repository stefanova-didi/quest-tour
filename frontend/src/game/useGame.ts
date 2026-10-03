import { useCallback, useEffect, useRef, useState } from "react";
import { api, HttpError, isConnectionProblem, LinkNotValidError } from "../api/client";
import type { ActionResult, GameState, LinkNotValidInfo, Outcome } from "../api/types";
import { teammateNotice } from "./teammateNotice";

export const POLL_MS = 60_000;
export const RETRY_MS = 5_000;
const TEAMMATE_OUTCOMES: Outcome[] = ["stale", "already_started", "game_over"];
const UNKNOWN_LINK: LinkNotValidInfo = {
  code: "link_not_valid", reason: "unknown", opens_at: null, expired_at: null, time_zone: null };

/** "offline" = the action produced no result (network/5xx, link invalid, or an unexpected 4xx). */
export type ActOutcome = Outcome | "offline";

export type View =
  | { kind: "loading" }
  | { kind: "invalid"; info: LinkNotValidInfo }
  | { kind: "ready"; state: GameState; receivedAt: number };

export interface GameController {
  view: View;
  offline: boolean;
  notice: string | null;
  clearNotice(): void;
  refresh(): Promise<void>;
  act(run: () => Promise<ActionResult>): Promise<ActOutcome>;
  /** Wraps a request made outside `act` (photo upload) so polls during it don't raise teammate toasts. */
  track<T>(request: Promise<T>): Promise<T>;
  applyResult(result: ActionResult): void;
  /** Routes an error from a request made outside `act` (LinkNotValid → invalid view, network → banner). */
  fail(err: unknown): void;
}

export function useGame(token: string): GameController {
  const [view, setView] = useState<View>({ kind: "loading" });
  const [offline, setOffline] = useState(false);
  const [notice, setNotice] = useState<string | null>(null);
  const current = useRef<GameState | null>(null);
  const retryTimer = useRef<number | undefined>(undefined);
  const inFlight = useRef(0);    // own actions currently awaiting a response
  // An own action failed on the network. The server may still have applied it (the response was lost),
  // so the next state this phone accepts must not be credited to "a teammate".
  const ownActionLost = useRef(false);
  const refreshRef = useRef<() => Promise<void>>(async () => {});

  const scheduleRetry = useCallback(() => {
    setOffline(true);
    window.clearTimeout(retryTimer.current);
    retryTimer.current = window.setTimeout(() => void refreshRef.current(), RETRY_MS);
  }, []);

  const accept = useCallback((next: GameState, fromTeammate: boolean) => {
    const prev = current.current;
    if (prev && next.version < prev.version) return;          // older than what is shown: ignore
    const maybeOwn = inFlight.current > 0 || ownActionLost.current;
    ownActionLost.current = false;                            // the first state after the failure settles it
    if (prev && fromTeammate && !maybeOwn) {
      const message = teammateNotice(prev, next);
      if (message) setNotice(message);
    }
    current.current = next;
    setView({ kind: "ready", state: next, receivedAt: Date.now() });
    setOffline(false);
    window.clearTimeout(retryTimer.current);
  }, []);

  const fail = useCallback((err: unknown) => {
    if (err instanceof LinkNotValidError) { setView({ kind: "invalid", info: err.info }); return; }
    if (isConnectionProblem(err)) { scheduleRetry(); return; }   // network / 5xx: banner + auto retry
    if (current.current === null && err instanceof HttpError) {
      // First load got an unexpected 4xx, e.g. a mangled link "/play/a%2Fb" hits a JSON 404 under /api.
      // Nothing to show, so the spinner would stay forever: treat it as an unknown link.
      setView({ kind: "invalid", info: UNKNOWN_LINK });
      return;
    }
    console.error(err);                                          // e.g. 422: a bug, not a connection problem
  }, [scheduleRetry]);

  const refresh = useCallback(async () => {
    try { accept(await api.state(token), true); } catch (err) { fail(err); }
  }, [token, accept, fail]);
  refreshRef.current = refresh;

  const track = useCallback(async <T,>(request: Promise<T>): Promise<T> => {
    inFlight.current += 1;
    try {
      return await request;
    } catch (err) {
      if (isConnectionProblem(err)) ownActionLost.current = true;   // answer or photo may have landed anyway
      throw err;
    } finally {
      inFlight.current -= 1;
    }
  }, []);

  const act = useCallback(async (run: () => Promise<ActionResult>): Promise<ActOutcome> => {
    try {
      const result = await track(run());
      accept(result.state, TEAMMATE_OUTCOMES.includes(result.outcome));
      return result.outcome;
    } catch (err) {
      fail(err);                       // track() has already flagged a lost own action
      return "offline";
    }
  }, [accept, fail, track]);

  const applyResult = useCallback((result: ActionResult) => {
    accept(result.state, TEAMMATE_OUTCOMES.includes(result.outcome));
  }, [accept]);

  const clearNotice = useCallback(() => setNotice(null), []);   // stable: Toast's timer must not restart

  useEffect(() => {
    void refresh();
    const interval = window.setInterval(() => void refresh(), POLL_MS);
    const onVisible = () => { if (document.visibilityState === "visible") void refresh(); };
    const onOnline = () => void refresh();
    const onOffline = () => setOffline(true);                   // show the banner without waiting for a failure
    document.addEventListener("visibilitychange", onVisible);
    window.addEventListener("online", onOnline);
    window.addEventListener("offline", onOffline);
    return () => {
      window.clearInterval(interval);
      window.clearTimeout(retryTimer.current);
      document.removeEventListener("visibilitychange", onVisible);
      window.removeEventListener("online", onOnline);
      window.removeEventListener("offline", onOffline);
    };
  }, [refresh]);

  return { view, offline, notice, clearNotice, refresh, act, track, applyResult, fail };
}
