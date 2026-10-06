import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, vi } from "vitest";
import { makeState, makeTask } from "../test/fixtures";
import { TaskScreen } from "./TaskScreen";

const frame = { header: null, offline: false, notice: null, onNoticeDone: () => {} };

afterEach(() => {
  vi.unstubAllGlobals();
});

it("confirms the hint penalty before opening it", async () => {
  const onHint = vi.fn().mockResolvedValue("ok");
  render(<TaskScreen state={makeState()} receivedAt={Date.now()} frame={frame}
                     onAnswer={vi.fn()} onHint={onHint} onReveal={vi.fn()} onCompass={vi.fn().mockResolvedValue("ok")} />);
  await userEvent.click(screen.getByRole("button", { name: /Hint 1/ }));
  expect(screen.getByRole("dialog", { name: "Open hint 1?" })).toBeInTheDocument();
  await userEvent.click(screen.getByRole("button", { name: "Open hint" }));
  expect(onHint).toHaveBeenCalledWith(1);
});

it("shows 'Not quite – try again' and keeps the typed text", async () => {
  const onAnswer = vi.fn().mockResolvedValue("wrong");
  render(<TaskScreen state={makeState()} receivedAt={Date.now()} frame={frame}
                     onAnswer={onAnswer} onHint={vi.fn()} onReveal={vi.fn()} onCompass={vi.fn().mockResolvedValue("ok")} />);
  await userEvent.type(screen.getByLabelText("Your answer"), "Saint Sofia Church");
  await userEvent.click(screen.getByRole("button", { name: "Submit" }));
  expect(await screen.findByText("Not quite – try again")).toBeInTheDocument();
  expect(screen.getByLabelText("Your answer")).toHaveValue("Saint Sofia Church");
});

it("keeps reveal locked until unlocked, then uses the danger confirm", async () => {
  const { rerender } = render(<TaskScreen state={makeState()} receivedAt={Date.now()} frame={frame}
                                          onAnswer={vi.fn()} onHint={vi.fn()} onReveal={vi.fn()} onCompass={vi.fn().mockResolvedValue("ok")} />);
  expect(screen.getByRole("button", { name: /Reveal answer/ })).toBeDisabled();
  rerender(<TaskScreen state={makeState({ task: makeTask({ reveal_unlocked: true, reveal_unlocks_in_seconds: null }) })}
                       receivedAt={Date.now()} frame={frame} onAnswer={vi.fn()} onHint={vi.fn()} onReveal={vi.fn()} onCompass={vi.fn().mockResolvedValue("ok")} />);
  await userEvent.click(screen.getByRole("button", { name: /Give up and reveal answer/ }));
  expect(screen.getByRole("button", { name: "Reveal" })).toHaveClass("qc-btn--danger");
});

it("shows an opened hint's text and does not submit an empty answer", async () => {
  const onAnswer = vi.fn();
  const task = makeTask({ hints: [
    { number: 1, penalty_minutes: 10, available: false, opened: true, text: "Look for the golden domes." },
    { number: 2, penalty_minutes: 15, available: true, opened: false, text: null },
  ] });
  render(<TaskScreen state={makeState({ task })} receivedAt={Date.now()} frame={frame}
                     onAnswer={onAnswer} onHint={vi.fn()} onReveal={vi.fn()} onCompass={vi.fn().mockResolvedValue("ok")} />);
  expect(screen.getByText("Look for the golden domes.")).toBeInTheDocument();
  await userEvent.click(screen.getByRole("button", { name: "Submit" }));
  expect(onAnswer).not.toHaveBeenCalled();
});

it("confirms the compass penalty before opening it", async () => {
  const onCompass = vi.fn().mockResolvedValue("ok");
  const task = makeTask({ compass: { opened: false, lat: 42.7, lon: 23.3, penalty_minutes: 5 } });
  render(<TaskScreen state={makeState({ task })} receivedAt={Date.now()} frame={frame}
                     onAnswer={vi.fn()} onHint={vi.fn()} onReveal={vi.fn()} onCompass={onCompass} />);
  await userEvent.click(screen.getByRole("button", { name: /Compass/ }));
  expect(screen.getByRole("dialog", { name: "Open compass?" })).toBeInTheDocument();
  await userEvent.click(screen.getByRole("button", { name: "Open compass" }));
  expect(onCompass).toHaveBeenCalled();
});

it("requests iOS device-orientation permission before opening the compass", async () => {
  const requestPermission = vi.fn().mockResolvedValue("granted");
  vi.stubGlobal("DeviceOrientationEvent", { requestPermission });
  const onCompass = vi.fn().mockResolvedValue("ok");
  const task = makeTask({ compass: { opened: false, lat: 42.7, lon: 23.3, penalty_minutes: 5 } });
  render(<TaskScreen state={makeState({ task })} receivedAt={Date.now()} frame={frame}
                     onAnswer={vi.fn()} onHint={vi.fn()} onReveal={vi.fn()} onCompass={onCompass} />);
  await userEvent.click(screen.getByRole("button", { name: /Compass/ }));
  await userEvent.click(screen.getByRole("button", { name: "Open compass" }));
  expect(requestPermission).toHaveBeenCalledTimes(1);
  expect(onCompass).toHaveBeenCalled();
  // The permission prompt must be inside the user gesture, i.e. before the server call.
  expect(requestPermission.mock.invocationCallOrder[0])
    .toBeLessThan(onCompass.mock.invocationCallOrder[0]);
});

it("still opens the compass when the iOS permission is denied", async () => {
  const requestPermission = vi.fn().mockRejectedValue(new Error("denied"));
  vi.stubGlobal("DeviceOrientationEvent", { requestPermission });
  const onCompass = vi.fn().mockResolvedValue("ok");
  const task = makeTask({ compass: { opened: false, lat: 42.7, lon: 23.3, penalty_minutes: 5 } });
  render(<TaskScreen state={makeState({ task })} receivedAt={Date.now()} frame={frame}
                     onAnswer={vi.fn()} onHint={vi.fn()} onReveal={vi.fn()} onCompass={onCompass} />);
  await userEvent.click(screen.getByRole("button", { name: /Compass/ }));
  await userEvent.click(screen.getByRole("button", { name: "Open compass" }));
  expect(onCompass).toHaveBeenCalled(); // falls back to the static bearing text
});

it("hides the compass button when no compass is available", () => {
  render(<TaskScreen state={makeState()} receivedAt={Date.now()} frame={frame}
                     onAnswer={vi.fn()} onHint={vi.fn()} onReveal={vi.fn()} onCompass={vi.fn().mockResolvedValue("ok")} />);
  expect(screen.queryByRole("button", { name: /Compass/ })).not.toBeInTheDocument();
});
