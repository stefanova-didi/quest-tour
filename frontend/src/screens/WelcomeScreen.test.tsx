import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { vi } from "vitest";
import { makeState } from "../test/fixtures";
import { WelcomeScreen } from "./WelcomeScreen";

const frame = { header: null, offline: false, notice: null, onNoticeDone: () => {} };

it("lists the rules with the reveal penalty from the game settings", () => {
  render(<WelcomeScreen state={makeState({ phase: null, status: "not_started", clock: null, task: null })} frame={frame} onStart={vi.fn()} />);
  expect(screen.getByText("+30 min")).toBeInTheDocument();
  expect(screen.getByText(/You have up to 4 hours\./)).toBeInTheDocument();
  expect(screen.getByText("A city quest in 8 riddles")).toBeInTheDocument();
  expect(screen.getByRole("heading", { name: "Sofia Old Town Quest" })).toBeInTheDocument();
});

it("asks for confirmation before calling onStart", async () => {
  const onStart = vi.fn().mockResolvedValue("ok");
  render(<WelcomeScreen state={makeState({ phase: null, status: "not_started", clock: null, task: null })} frame={frame} onStart={onStart} />);
  await userEvent.click(screen.getByRole("button", { name: "Start the quest" }));
  expect(screen.getByRole("dialog", { name: "Start the clock?" })).toBeInTheDocument();
  expect(onStart).not.toHaveBeenCalled();
  await userEvent.click(screen.getByRole("button", { name: "Start" }));
  expect(onStart).toHaveBeenCalledTimes(1);
});
