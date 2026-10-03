import { render, screen } from "@testing-library/react";
import { beforeEach, describe, expect, it } from "vitest";
import { App } from "./App";

describe("App", () => {
  beforeEach(() => localStorage.clear());

  it("shows the 404 page for an unknown path", () => {
    render(<App path="/no/such/page" />);
    expect(screen.getByText("Page not found")).toBeInTheDocument();
    expect(screen.getByText("Error 404")).toBeInTheDocument();
  });

  it("asks for the game link at / when no token is remembered", () => {
    render(<App path="/" />);
    expect(screen.getByText("Open your game link")).toBeInTheDocument();
    expect(screen.queryByText("Error 404")).not.toBeInTheDocument();
  });

  it("shows the 404 page for a mangled %-escape in the token", () => {
    render(<App path="/play/%E0%A4%A" />);
    expect(screen.getByText("Page not found")).toBeInTheDocument();
  });
});
