import { render, screen } from "@testing-library/react";
import { APP_VERSION, versionLabel } from "../lib/version";
import { AppVersion } from "./AppVersion";

it("shows the build version in a footer", () => {
  render(<AppVersion />);
  const footer = screen.getByRole("contentinfo");
  expect(footer).toHaveTextContent("Quest City Tour");
  expect(screen.getByTestId("app-version")).toHaveTextContent(versionLabel(APP_VERSION));
  expect(footer).not.toHaveClass("qs-version--inverse");
});

it("has an inverse variant for the dark bands", () => {
  render(<AppVersion inverse />);
  expect(screen.getByRole("contentinfo")).toHaveClass("qs-version--inverse");
});
