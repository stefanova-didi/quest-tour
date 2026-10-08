import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { vi } from "vitest";
import { makeState } from "../test/fixtures";
import { CoverScreen } from "./CoverScreen";

const frame = { header: null, offline: false, notice: null, onNoticeDone: () => {} };
const notStarted = () => makeState({ phase: null, status: "not_started", clock: null, task: null });

it("shows the game name, the riddle count and the team", () => {
  render(<CoverScreen state={notStarted()} frame={frame} onContinue={vi.fn()} />);
  expect(screen.getByRole("heading", { name: "Sofia Old Town Quest" })).toBeInTheDocument();
  expect(screen.getByText("A city quest in 8 riddles")).toBeInTheDocument();
  expect(screen.getByText("Welcome, The Explorers")).toBeInTheDocument();
});

it("has one button, which continues to the Welcome page", async () => {
  const onContinue = vi.fn();
  render(<CoverScreen state={notStarted()} frame={frame} onContinue={onContinue} />);
  expect(screen.getAllByRole("button")).toHaveLength(1);
  await userEvent.click(screen.getByRole("button", { name: "How it works" }));
  expect(onContinue).toHaveBeenCalledTimes(1);
});
