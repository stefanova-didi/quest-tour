import { render, screen, waitFor } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { adminApi } from "../api";
import { Dashboard } from "./Dashboard";

vi.mock("../api", async (importOriginal) => ({
  ...(await importOriginal<typeof import("../api")>()),
  adminApi: {
    seedError: vi.fn(),
  },
}));

describe("Dashboard", () => {
  beforeEach(() => {
    vi.mocked(adminApi.seedError).mockReset();
  });

  it("shows seed error banner when present", async () => {
    vi.mocked(adminApi.seedError).mockResolvedValueOnce({ error: "Missing fixture" });
    render(<Dashboard />);

    await waitFor(() => {
      expect(screen.getByText(/Missing fixture/)).toBeInTheDocument();
    });
  });

  it("shows navigation when there is no seed error", async () => {
    vi.mocked(adminApi.seedError).mockResolvedValueOnce({ error: null });
    render(<Dashboard />);

    await waitFor(() => {
      expect(screen.getByRole("link", { name: "Landmarks" })).toBeInTheDocument();
    });
    expect(screen.getByRole("link", { name: "Games" })).toBeInTheDocument();
    expect(screen.getByRole("link", { name: "Teams" })).toBeInTheDocument();
    expect(screen.getByRole("link", { name: "Photos" })).toBeInTheDocument();
  });
});
