import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { vi } from "vitest";
import { api, HttpError, LinkNotValidError, NetworkError } from "../api/client";
import { AlbumPage } from "./AlbumPage";
import { MOCK_ALBUM } from "./mock";
import type { Album } from "./types";

vi.mock("../api/client", async (importOriginal) => {
  const original = await importOriginal<typeof import("../api/client")>();
  return { ...original, api: { ...original.api, album: vi.fn() } };
});

const album: Album = {
  ...MOCK_ALBUM, team: "Night Owls", chapters: MOCK_ALBUM.chapters.slice(0, 2),
};

beforeEach(() => { vi.mocked(api.album).mockReset(); localStorage.clear(); });

it("renders the mock album for the preview token without calling the API", () => {
  render(<AlbumPage token="preview" />);
  expect(screen.getByRole("heading", { level: 1, name: MOCK_ALBUM.game })).toBeInTheDocument();
  expect(api.album).not.toHaveBeenCalled();
});

it("loads the team's album from the API for a real token", async () => {
  vi.mocked(api.album).mockResolvedValueOnce(album);
  render(<AlbumPage token="explorers-token" />);
  expect(await screen.findByRole("heading", { level: 2, name: "Night Owls" })).toBeInTheDocument();
  expect(api.album).toHaveBeenCalledWith("explorers-token");
  expect(screen.getAllByRole("region", { name: /^(Lily Pond|Eagles' Bridge)$/ })).toHaveLength(2);
});

it("explains that the album is not ready while the game is still on (409)", async () => {
  vi.mocked(api.album).mockRejectedValueOnce(new HttpError(409));
  render(<AlbumPage token="explorers-token" />);
  expect(await screen.findByText("Your album isn't ready yet")).toBeInTheDocument();
});

it("shows the link-not-valid screen for an unknown link", async () => {
  vi.mocked(api.album).mockRejectedValueOnce(new LinkNotValidError({ code: "link_not_valid", reason: "unknown", opens_at: null, expired_at: null, time_zone: null }));
  render(<AlbumPage token="nope" />);
  expect(await screen.findByRole("heading", { name: "This game link isn't active" })).toBeInTheDocument();
  expect(screen.queryByText("Your album isn't ready yet")).not.toBeInTheDocument();
});

it("offers a retry when the album could not be loaded", async () => {
  vi.mocked(api.album).mockRejectedValueOnce(new NetworkError()).mockResolvedValueOnce(album);
  render(<AlbumPage token="explorers-token" />);
  await userEvent.click(await screen.findByRole("button", { name: "Try again" }));
  expect(await screen.findByRole("heading", { level: 2, name: "Night Owls" })).toBeInTheDocument();
  expect(api.album).toHaveBeenCalledTimes(2);
});

it("shows the stories in the chosen language", async () => {
  vi.mocked(api.album).mockResolvedValueOnce(album);
  render(<AlbumPage token="explorers-token" />);
  await screen.findByRole("heading", { level: 2, name: "Night Owls" });
  await userEvent.click(screen.getByRole("button", { name: "Language, EN" }));
  await userEvent.click(screen.getByRole("option", { name: "Deutsch" }));
  expect(screen.getByRole("heading", { level: 2, name: "Seerosenteich" })).toBeInTheDocument();
});
