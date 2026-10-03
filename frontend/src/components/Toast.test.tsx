import { act, fireEvent, render, screen } from "@testing-library/react";
import { afterEach, beforeEach, expect, it, vi } from "vitest";
import { Toast } from "./Toast";

beforeEach(() => { vi.useFakeTimers(); });
afterEach(() => { vi.useRealTimers(); });

it("dismisses itself after 5 seconds", () => {
  const onDone = vi.fn();
  render(<Toast message="A teammate solved this task" onDone={onDone} />);
  expect(screen.getByText("A teammate solved this task")).toBeInTheDocument();
  act(() => { vi.advanceTimersByTime(4999); });
  expect(onDone).not.toHaveBeenCalled();
  act(() => { vi.advanceTimersByTime(1); });
  expect(onDone).toHaveBeenCalledTimes(1);
});

it("can be closed with the X button and sits higher on the task screen", () => {
  const onDone = vi.fn();
  const { container } = render(<Toast message="hi" onDone={onDone} high />);
  expect(container.firstElementChild).toHaveClass("qs-toast-slot--high");
  fireEvent.click(screen.getByRole("button", { name: "Dismiss" }));
  expect(onDone).toHaveBeenCalledTimes(1);
});
