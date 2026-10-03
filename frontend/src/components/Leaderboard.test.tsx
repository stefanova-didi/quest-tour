import { render, screen } from "@testing-library/react";
import { expect, it } from "vitest";
import { Leaderboard } from "./Leaderboard";
import { Paragraphs } from "./Paragraphs";

it("renders rows and marks the viewer's team", () => {
  render(<Leaderboard gameName="Sofia Old Town Quest" rows={[
    { rank: 1, team_name: "Night Owls", total_seconds: 9665, hints_used: 1, is_you: false },
    { rank: 2, team_name: "The Explorers", total_seconds: 10710, hints_used: 3, is_you: true },
  ]} />);
  expect(screen.getByText("02:41:05")).toBeInTheDocument();
  expect(screen.getByText("You").closest("tr")).toHaveClass("is-you");
  expect(screen.getByText("Teams that finished Sofia Old Town Quest")).toBeInTheDocument();
});

it("shows an empty message without rows", () => {
  render(<Leaderboard rows={[]} gameName="G" />);
  expect(screen.getByText("No team has finished yet.")).toBeInTheDocument();
});

it("renders paragraphs as text, never as HTML", () => {
  const { container } = render(<Paragraphs text={"one\n\n<b>two</b>"} />);
  expect(container.querySelectorAll("p")).toHaveLength(2);
  expect(container.querySelector("b")).toBeNull();
  expect(screen.getByText("<b>two</b>")).toBeInTheDocument();
});
