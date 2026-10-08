import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { expect, test, vi } from "vitest";
import { LanguageToggle } from "./LanguageToggle";

test("shows only the selected language until the menu is opened", () => {
  render(<LanguageToggle languages={["de", "sr"]} selected="en" onSelect={() => {}} />);
  expect(screen.getByRole("button", { name: "Language, EN" })).toBeInTheDocument();
  expect(screen.queryByRole("option", { name: "DE" })).not.toBeInTheDocument();
});

test("opening the menu lists every language and selects on click", async () => {
  const user = userEvent.setup();
  const onSelect = vi.fn();
  render(<LanguageToggle languages={["de", "sr"]} selected="en" onSelect={onSelect} />);
  await user.click(screen.getByRole("button", { name: "Language, EN" }));
  expect(screen.getByRole("option", { name: "EN" })).toBeInTheDocument();
  expect(screen.getByRole("option", { name: "DE" })).toBeInTheDocument();
  expect(screen.getByRole("option", { name: "SR" })).toBeInTheDocument();
  await user.click(screen.getByRole("option", { name: "SR" }));
  expect(onSelect).toHaveBeenCalledWith("sr");
  expect(screen.queryByRole("option", { name: "SR" })).not.toBeInTheDocument();
});

test("marks the current language as selected in the menu", async () => {
  const user = userEvent.setup();
  render(<LanguageToggle languages={["de"]} selected="de" onSelect={() => {}} />);
  expect(screen.getByRole("button", { name: "Language, DE" })).toBeInTheDocument();
  await user.click(screen.getByRole("button", { name: "Language, DE" }));
  expect(screen.getByRole("option", { name: "DE" })).toHaveAttribute("aria-selected", "true");
  expect(screen.getByRole("option", { name: "EN" })).toHaveAttribute("aria-selected", "false");
});

test("closes the menu on Escape without changing the selection", async () => {
  const user = userEvent.setup();
  const onSelect = vi.fn();
  render(<LanguageToggle languages={["de"]} selected="en" onSelect={onSelect} />);
  await user.click(screen.getByRole("button", { name: "Language, EN" }));
  await user.keyboard("{Escape}");
  expect(screen.queryByRole("option", { name: "DE" })).not.toBeInTheDocument();
  expect(onSelect).not.toHaveBeenCalled();
});
