import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { AdminLayout } from "./AdminLayout";
import { adminApi } from "../api";

vi.mock("../api", () => ({
  adminApi: {
    logout: vi.fn(),
  },
}));

describe("AdminLayout", () => {
  beforeEach(() => {
    vi.mocked(adminApi.logout).mockReset();
    vi.stubGlobal("location", { href: "" });
  });

  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it("renders a Logout button", () => {
    render(<AdminLayout active="dashboard">Content</AdminLayout>);
    expect(screen.getByRole("button", { name: "Logout" })).toBeInTheDocument();
  });

  it("calls logout and redirects to login when Logout is clicked", async () => {
    const user = userEvent.setup();
    vi.mocked(adminApi.logout).mockResolvedValueOnce({ ok: true });

    render(<AdminLayout active="dashboard">Content</AdminLayout>);
    await user.click(screen.getByRole("button", { name: "Logout" }));

    await waitFor(() => {
      expect(adminApi.logout).toHaveBeenCalled();
    });
    await waitFor(() => {
      expect(window.location.href).toBe("/admin/login");
    });
  });
});
