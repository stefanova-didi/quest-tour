import { expect, it } from "vitest";
import { makeState, makeTask, NEVSKY } from "../test/fixtures";
import { teammateNotice } from "./teammateNotice";

it("explains changes made on another phone", () => {
  const task = makeState();
  expect(teammateNotice(task, makeState({ phase: "photo", task: makeTask({ completion: "answered", landmark: NEVSKY }) })))
    .toBe("A teammate solved this task");
  expect(teammateNotice(task, makeState({ phase: "photo", task: makeTask({ completion: "revealed", landmark: NEVSKY }) })))
    .toBe("A teammate revealed the answer");
  const hinted = makeTask({ hints: [{ number: 1, penalty_minutes: 10, available: false, opened: true, text: "x" },
                                    { number: 2, penalty_minutes: 15, available: true, opened: false, text: null }] });
  expect(teammateNotice(task, makeState({ task: hinted }))).toBe("A teammate opened hint 1");
  expect(teammateNotice(task, makeState({ position: 3 }))).toBe("A teammate moved on to the next riddle");
  expect(teammateNotice(makeState({ status: "not_started", phase: null }), task)).toBe("A teammate started the quest");
  expect(teammateNotice(task, task)).toBeNull();
});
