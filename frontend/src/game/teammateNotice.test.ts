import { expect, it } from "vitest";
import { makeState, makeTask, NEVSKY } from "../test/fixtures";
import { teammateNotice } from "./teammateNotice";

it("explains changes made on another phone", () => {
  const task = makeState();
  expect(teammateNotice(task, makeState({ phase: "photo", task: makeTask({ completion: "answered", landmark: NEVSKY }) })))
    .toBe("A teammate solved this task");
  expect(teammateNotice(task, makeState({ phase: "photo", task: makeTask({ completion: "revealed", landmark: NEVSKY }) })))
    .toBe("A teammate revealed the answer");
  const hinted = makeTask({ hints: [{ number: 1, penalty_minutes: 10, available: false, opened: true, text: "x", text_i18n: {} },
                                    { number: 2, penalty_minutes: 15, available: true, opened: false, text: null, text_i18n: {} }] });
  expect(teammateNotice(task, makeState({ task: hinted }))).toBe("A teammate opened hint 1");
  expect(teammateNotice(task, makeState({ position: 3 }))).toBe("A teammate moved on to the next riddle");
  const compassOpened = makeTask({ compass: { opened: true, lat: 42.7, lon: 23.3, penalty_minutes: 5 } });
  expect(teammateNotice(task, makeState({ task: compassOpened }))).toBe("A teammate opened the compass");
  expect(teammateNotice(makeState({ status: "not_started", phase: null }), task)).toBe("A teammate started the quest");
  expect(teammateNotice(task, task)).toBeNull();
});

it("tells teammates that the test run was reset", () => {
  const reset = makeState({ status: "not_started", phase: null, position: 0, clock: null, task: null, service: true });
  expect(teammateNotice(makeState({ service: true }), reset)).toBe("The test run was reset");
});
