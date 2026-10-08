import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { expect, it, vi } from "vitest";
import { GameHeader } from "./GameHeader";

const base = { elapsed_seconds: 4365, running: true, penalty_minutes: 25, remaining_seconds: 10035, warning: false };
const common = { availableLanguages: ["de", "sr"], language: "en", onLanguageChange: () => {} };

it("shows clock, penalty and progress", () => {
  render(<GameHeader clock={base} position={2} taskCount={8} receivedAt={Date.now()} onTimeUp={() => {}} {...common} />);
  expect(screen.getByText("01:12:45")).toBeInTheDocument();
  expect(screen.getByText("+25 min")).toBeInTheDocument();
  expect(screen.getByText("Task 3 of 8")).toBeInTheDocument();
  expect(screen.getByRole("progressbar")).toHaveAttribute("aria-valuenow", "3");
});

it("hides the penalty tag at zero and switches to warning in the last 15 minutes", () => {
  render(<GameHeader clock={{ ...base, penalty_minutes: 0, elapsed_seconds: 13640, remaining_seconds: 760 }}
                     position={6} taskCount={8} receivedAt={Date.now()} onTimeUp={() => {}} {...common} />);
  expect(screen.queryByText(/\+\d+ min/)).toBeNull();
  expect(screen.getByText("12:40 left")).toBeInTheDocument();
  expect(screen.getByRole("banner")).toHaveClass("qc-header--warning");
});

it("asks the server once when the local countdown reaches zero", () => {
  const onTimeUp = vi.fn();
  const clock = { ...base, remaining_seconds: 0 };
  const { rerender } = render(<GameHeader clock={clock} position={1} taskCount={8} receivedAt={5} onTimeUp={onTimeUp} {...common} />);
  rerender(<GameHeader clock={clock} position={1} taskCount={8} receivedAt={5} onTimeUp={onTimeUp} {...common} />);
  expect(onTimeUp).toHaveBeenCalledTimes(1);
});

it("renders the language menu with available languages", async () => {
  const user = userEvent.setup();
  render(<GameHeader clock={base} position={0} taskCount={8} receivedAt={Date.now()} onTimeUp={() => {}} {...common} />);
  expect(screen.getByRole("button", { name: "Language, EN" })).toBeInTheDocument();
  await user.click(screen.getByRole("button", { name: "Language, EN" }));
  expect(screen.getByRole("option", { name: "EN" })).toBeInTheDocument();
  expect(screen.getByRole("option", { name: "DE" })).toBeInTheDocument();
  expect(screen.getByRole("option", { name: "SR" })).toBeInTheDocument();
});
