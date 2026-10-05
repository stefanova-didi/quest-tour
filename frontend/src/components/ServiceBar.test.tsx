import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { expect, it, vi } from "vitest";
import { ServiceBar } from "./ServiceBar";

it("confirms before resetting the test run", async () => {
  const onReset = vi.fn().mockResolvedValue("ok");
  render(<ServiceBar onReset={onReset} />);
  expect(screen.getByText("Test link · no time limits")).toBeInTheDocument();
  await userEvent.click(screen.getByRole("button", { name: "Reset test run" }));
  expect(screen.getByRole("dialog", { name: "Reset this test run?" })).toBeInTheDocument();
  expect(onReset).not.toHaveBeenCalled();
  await userEvent.click(screen.getByRole("button", { name: "Reset" }));
  expect(onReset).toHaveBeenCalledTimes(1);
  expect(screen.queryByRole("dialog")).not.toBeInTheDocument();
});

it("cancel keeps the run", async () => {
  const onReset = vi.fn();
  render(<ServiceBar onReset={onReset} />);
  await userEvent.click(screen.getByRole("button", { name: "Reset test run" }));
  await userEvent.click(screen.getByRole("button", { name: "Cancel" }));
  expect(onReset).not.toHaveBeenCalled();
  expect(screen.queryByRole("dialog")).not.toBeInTheDocument();
});
