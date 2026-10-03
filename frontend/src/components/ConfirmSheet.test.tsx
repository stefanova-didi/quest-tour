import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { expect, it, vi } from "vitest";
import { ConfirmSheet } from "./ConfirmSheet";

function setup(extra = {}) {
  const onConfirm = vi.fn();
  const onCancel = vi.fn();
  render(<ConfirmSheet title="Open hint 1?" body="This adds time." confirmLabel="Open hint"
                       onConfirm={onConfirm} onCancel={onCancel} {...extra} />);
  return { onConfirm, onCancel };
}

it("confirms, cancels and closes on Escape or backdrop click", async () => {
  const { onConfirm, onCancel } = setup();
  const user = userEvent.setup();
  expect(screen.getByRole("dialog", { name: "Open hint 1?" })).toBeInTheDocument();
  expect(screen.getByRole("button", { name: "Open hint" })).toHaveFocus();
  await user.click(screen.getByRole("button", { name: "Open hint" }));
  expect(onConfirm).toHaveBeenCalledTimes(1);
  await user.click(screen.getByRole("button", { name: "Cancel" }));
  await user.keyboard("{Escape}");
  await user.click(document.querySelector(".qc-scrim")!);
  expect(onCancel).toHaveBeenCalledTimes(3);
});

it("disables the confirm button while busy", () => {
  setup({ busy: true });
  expect(screen.getByRole("button", { name: "Open hint" })).toBeDisabled();
});
