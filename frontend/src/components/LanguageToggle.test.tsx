import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { expect, test, vi } from "vitest";
import { LanguageToggle } from "./LanguageToggle";

test("renders base plus available languages and calls onSelect", async () => {
  const user = userEvent.setup();
  const onSelect = vi.fn();
  render(<LanguageToggle languages={["de", "sr"]} selected="en" onSelect={onSelect} />);
  await user.click(screen.getByRole("button", { name: "DE" }));
  expect(onSelect).toHaveBeenCalledWith("de");
});

test("marks selected language as pressed", () => {
  render(<LanguageToggle languages={["de"]} selected="de" onSelect={() => {}} />);
  expect(screen.getByRole("button", { name: "DE" })).toHaveAttribute("aria-pressed", "true");
  expect(screen.getByRole("button", { name: "Base / EN" })).toHaveAttribute("aria-pressed", "false");
});
