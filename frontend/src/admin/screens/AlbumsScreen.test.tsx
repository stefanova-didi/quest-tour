import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { adminApi } from "../api";
import type { AlbumRowOut } from "../types";
import { AlbumsScreen } from "./AlbumsScreen";

vi.mock("../api", async (importOriginal) => ({
  ...(await importOriginal<typeof import("../api")>()),
  adminApi: { albums: vi.fn(), generateAlbum: vi.fn(), deleteAlbum: vi.fn() },
}));

const withAlbum: AlbumRowOut = {
  assignment_id: 1, team_name: "The Explorers", game_name: "Sofia Old Town Quest",
  ended_at: "2026-10-03T10:28:30Z", end_reason: "finished", photo_count: 10,
  album: { id: 7, size_bytes: 2_400_000, generated_at: "2026-10-03T10:30:00Z", deleted_at: null, url: "http://test/api/admin/albums/7/download" },
};
const withoutAlbum: AlbumRowOut = {
  assignment_id: 2, team_name: "Night Owls", game_name: "Sofia Old Town Quest",
  ended_at: "2026-10-03T11:00:00Z", end_reason: "max_duration", photo_count: 3, album: null,
};

describe("AlbumsScreen", () => {
  beforeEach(() => {
    vi.mocked(adminApi.albums).mockReset();
    vi.mocked(adminApi.generateAlbum).mockReset();
    vi.mocked(adminApi.deleteAlbum).mockReset();
  });

  it("lists every run that has ended with its album state and actions", async () => {
    vi.mocked(adminApi.albums).mockResolvedValue([withAlbum, withoutAlbum]);
    render(<AlbumsScreen />);
    expect(await screen.findByText("The Explorers")).toBeInTheDocument();
    expect(screen.getByText(/PDF 2\.3 MB, generated/)).toBeInTheDocument();
    expect(screen.getByRole("link", { name: "Download" })).toHaveAttribute("href", "http://test/api/admin/albums/7/download");
    expect(screen.getByRole("button", { name: "Delete" })).toBeInTheDocument();
    expect(screen.getByText("No album yet")).toBeInTheDocument();
    expect(screen.getByText(/time ran out/)).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Generate" })).toBeInTheDocument();
  });

  it("generates an album for a run and reloads the list", async () => {
    vi.mocked(adminApi.albums).mockResolvedValue([withoutAlbum]);
    vi.mocked(adminApi.generateAlbum).mockResolvedValue({ ...withAlbum.album!, id: 9 });
    render(<AlbumsScreen />);
    await userEvent.click(await screen.findByRole("button", { name: "Generate" }));
    await waitFor(() => expect(adminApi.generateAlbum).toHaveBeenCalledWith(2));
    expect(adminApi.albums).toHaveBeenCalledTimes(2);
  });

  it("asks before deleting and then deletes the album", async () => {
    vi.mocked(adminApi.albums).mockResolvedValue([withAlbum]);
    vi.mocked(adminApi.deleteAlbum).mockResolvedValue({ deleted: true });
    render(<AlbumsScreen />);
    await userEvent.click(await screen.findByRole("button", { name: "Delete" }));
    expect(screen.getByText("Delete the album of The Explorers?")).toBeInTheDocument();
    expect(adminApi.deleteAlbum).not.toHaveBeenCalled();
    await userEvent.click(screen.getAllByRole("button", { name: "Delete" }).at(-1)!);
    await waitFor(() => expect(adminApi.deleteAlbum).toHaveBeenCalledWith(7));
  });

  it("shows a deleted album as deleted, with Generate but no Download", async () => {
    vi.mocked(adminApi.albums).mockResolvedValue([{ ...withAlbum, album: { ...withAlbum.album!, deleted_at: "2026-10-05T09:00:00Z" } }]);
    render(<AlbumsScreen />);
    expect(await screen.findByText(/Album deleted/)).toBeInTheDocument();
    expect(screen.queryByRole("link", { name: "Download" })).not.toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Generate" })).toBeInTheDocument();
  });
});
