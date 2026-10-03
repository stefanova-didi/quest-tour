import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { vi } from "vitest";
import { makeState, makeTask } from "../test/fixtures";
import { TaskScreen } from "./TaskScreen";

const frame = { header: null, offline: false, notice: null, onNoticeDone: () => {} };

it("confirms the hint penalty before opening it", async () => {
  const onHint = vi.fn().mockResolvedValue("ok");
  render(<TaskScreen state={makeState()} receivedAt={Date.now()} frame={frame}
                     onAnswer={vi.fn()} onHint={onHint} onReveal={vi.fn()} />);
  await userEvent.click(screen.getByRole("button", { name: /Hint 1/ }));
  expect(screen.getByRole("dialog", { name: "Open hint 1?" })).toBeInTheDocument();
  await userEvent.click(screen.getByRole("button", { name: "Open hint" }));
  expect(onHint).toHaveBeenCalledWith(1);
});

it("shows 'Not quite – try again' and keeps the typed text", async () => {
  const onAnswer = vi.fn().mockResolvedValue("wrong");
  render(<TaskScreen state={makeState()} receivedAt={Date.now()} frame={frame}
                     onAnswer={onAnswer} onHint={vi.fn()} onReveal={vi.fn()} />);
  await userEvent.type(screen.getByLabelText("Your answer"), "Saint Sofia Church");
  await userEvent.click(screen.getByRole("button", { name: "Submit" }));
  expect(await screen.findByText("Not quite – try again")).toBeInTheDocument();
  expect(screen.getByLabelText("Your answer")).toHaveValue("Saint Sofia Church");
});

it("keeps reveal locked until unlocked, then uses the danger confirm", async () => {
  const { rerender } = render(<TaskScreen state={makeState()} receivedAt={Date.now()} frame={frame}
                                          onAnswer={vi.fn()} onHint={vi.fn()} onReveal={vi.fn()} />);
  expect(screen.getByRole("button", { name: /Reveal answer/ })).toBeDisabled();
  rerender(<TaskScreen state={makeState({ task: makeTask({ reveal_unlocked: true, reveal_unlocks_in_seconds: null }) })}
                       receivedAt={Date.now()} frame={frame} onAnswer={vi.fn()} onHint={vi.fn()} onReveal={vi.fn()} />);
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
                     onAnswer={onAnswer} onHint={vi.fn()} onReveal={vi.fn()} />);
  expect(screen.getByText("Look for the golden domes.")).toBeInTheDocument();
  await userEvent.click(screen.getByRole("button", { name: "Submit" }));
  expect(onAnswer).not.toHaveBeenCalled();
});
