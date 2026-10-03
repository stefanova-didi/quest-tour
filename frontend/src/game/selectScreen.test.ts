import { describe, expect, it } from "vitest";
import { makeState, makeTask, NEVSKY } from "../test/fixtures";
import { EMPTY_UI, selectScreen } from "./selectScreen";

describe("selectScreen", () => {
  it("routes by status", () => {
    expect(selectScreen(makeState({ status: "not_started", phase: null, clock: null, task: null }), EMPTY_UI)).toBe("welcome");
    expect(selectScreen(makeState({ status: "timed_out", phase: "results" }), EMPTY_UI)).toBe("timesup");
    expect(selectScreen(makeState({ status: "finished", phase: "results" }), EMPTY_UI)).toBe("finish");
    expect(selectScreen(makeState(), EMPTY_UI)).toBe("task");
  });
  it("shows the celebration before the photo step until acknowledged", () => {
    const solved = makeState({ phase: "photo", task: makeTask({ completion: "answered", landmark: NEVSKY }) });
    expect(selectScreen(solved, EMPTY_UI)).toBe("correct");
    expect(selectScreen(solved, { ...EMPTY_UI, ackedPosition: 2 })).toBe("photo");
    const revealed = makeState({ phase: "photo", task: makeTask({ completion: "revealed", landmark: NEVSKY }) });
    expect(selectScreen(revealed, EMPTY_UI)).toBe("revealed");
  });
  it("keeps the uploader on 'Photo saved' until Continue", () => {
    const info = makeState({ phase: "info", task: makeTask({ completion: "answered", landmark: NEVSKY, photo_count: 1 }) });
    expect(selectScreen(info, { ...EMPTY_UI, photoFlowPosition: 2 })).toBe("photo");
    expect(selectScreen(info, EMPTY_UI)).toBe("landmark");
  });
});
