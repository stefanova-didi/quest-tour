import { render, screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { vi } from "vitest";
import { AlbumPage } from "./AlbumPage";
import { AlbumScreen } from "./AlbumScreen";
import { MOCK_ALBUM } from "./mock";
import type { Album } from "./types";

const album: Album = {
  game: "Sofia Old Town Quest", team: "The Explorers", time_zone: "Europe/Sofia",
  played_on: "2026-10-03T07:30:00Z", task_count: 6, total_seconds: 10710, rank: 2, shared_rank: false,
  host_message: "Thank you for exploring Sofia with us!\n\nHere is your journey.",
  chapters: [
    { number: 1, landmark: "Lily Pond", riddle: "Count the frogs.", story: "Laid out by Daniel Neff.\n\nKnown as the Fish Pond.",
      reached_at: "2026-10-03T07:58:00Z",
      photos: [{ url: "https://example.test/lily-1.jpg", taken_at: "2026-10-03T08:02:00Z" }] },
    { number: 2, landmark: "Eagles' Bridge", riddle: "Who guards the bridge?", story: "Built in 1891.",
      reached_at: "2026-10-03T08:22:00Z",
      photos: [
        { url: "https://example.test/bridge-1.jpg", taken_at: "2026-10-03T08:26:00Z" },
        { url: "https://example.test/bridge-2.jpg", taken_at: "2026-10-03T08:29:00Z" },
        { url: "https://example.test/bridge-3.jpg", taken_at: "2026-10-03T08:32:00Z" },
      ] },
  ],
};

it("opens with the game, the team and the facts of the day", () => {
  render(<AlbumScreen album={album} />);
  const cover = screen.getByRole("region", { name: "Cover" });
  expect(within(cover).getByRole("heading", { level: 1, name: "Sofia Old Town Quest" })).toBeInTheDocument();
  expect(within(cover).getByText("The Explorers")).toBeInTheDocument();
  const facts = within(cover).getByRole("list", { name: "The day in numbers" });
  expect(facts).toHaveTextContent("Saturday, 3 October 2026");
  expect(facts).toHaveTextContent("2 of 6 landmarks");
  expect(facts).toHaveTextContent("02:58:30");
  expect(facts).toHaveTextContent("2nd place");
  expect(screen.getByText("Thank you for exploring Sofia with us!")).toBeInTheDocument();
});

it("tells one chapter per landmark: time reached, photos with captions, riddle and story", () => {
  render(<AlbumScreen album={album} />);
  const chapter = screen.getByRole("region", { name: "Eagles' Bridge" });
  expect(chapter).toHaveTextContent("Landmark 2 of 6 · 11:22");
  const photos = within(chapter).getAllByRole("img");
  expect(photos).toHaveLength(3);
  expect(photos[0]).toHaveAttribute("alt", "The Explorers at Eagles' Bridge, 11:26");
  expect(within(chapter).getAllByText(/Team photo · /)).toHaveLength(3);
  expect(within(chapter).getByText("Who guards the bridge?")).toBeInTheDocument();
  expect(within(chapter).getByText("Built in 1891.")).toBeInTheDocument();
  expect(screen.getByRole("region", { name: "Lily Pond" })).toHaveTextContent("Known as the Fish Pond.");
});

it("leaves out the time and the place for a run that ended unfinished", () => {
  render(<AlbumScreen album={{ ...album, total_seconds: null, rank: null }} />);
  const facts = screen.getByRole("list", { name: "The day in numbers" });
  expect(facts).not.toHaveTextContent("02:58:30");
  expect(facts).not.toHaveTextContent("place");
});

it("closes with a contact sheet of every photo and numbered running feet", () => {
  const { container } = render(<AlbumScreen album={album} />);
  const contact = screen.getByLabelText("All the team's photos");
  expect(within(contact).getAllByRole("img")).toHaveLength(4);
  const feet = container.querySelectorAll(".qa-foot");
  expect(feet).toHaveLength(3);                               // two chapters and the end; the cover has none
  expect(feet[0]).toHaveTextContent("2 / 4");
  expect(feet[2]).toHaveTextContent("4 / 4");
});

it("offers Save as PDF in the toolbar and at the end, which opens the print dialog", async () => {
  const print = vi.spyOn(window, "print").mockImplementation(() => {});
  render(<AlbumScreen album={album} />);
  const buttons = screen.getAllByRole("button", { name: "Save as PDF" });
  expect(buttons).toHaveLength(2);
  await userEvent.click(buttons[0]);
  expect(print).toHaveBeenCalledTimes(1);
  print.mockRestore();
});

it("renders the mock album for the preview token and nothing else for any other token", () => {
  const { unmount } = render(<AlbumPage token="preview" />);
  expect(screen.getByRole("heading", { level: 1, name: MOCK_ALBUM.game })).toBeInTheDocument();
  expect(screen.getAllByRole("region").length).toBeGreaterThanOrEqual(MOCK_ALBUM.chapters.length);
  unmount();
  render(<AlbumPage token="someone-elses-token" />);
  expect(screen.getByText("Album not found")).toBeInTheDocument();
});
