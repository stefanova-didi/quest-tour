import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { adminApi, HttpErrorWithBody } from "../api";
import type { Landmark } from "../types";
import { LandmarksScreen } from "./LandmarksScreen";

vi.mock("../api", async (importOriginal) => ({
  ...(await importOriginal<typeof import("../api")>()),
  adminApi: {
    landmarks: vi.fn(),
    createLandmark: vi.fn(),
    updateLandmark: vi.fn(),
    deleteLandmark: vi.fn(),
    uploadLandmarkPicture: vi.fn(),
  },
}));

const landmark: Landmark = {
  id: 1,
  key: "nevsky",
  name: "Nevsky Prospekt",
  name_i18n: { de: "Nevsky Prospekt DE" },
  task: "Find the statue",
  task_i18n: { de: "Finde die Statue" },
  accepted_answers: ["statue"],
  hint1: "Look left",
  hint1_i18n: { de: "Schau links" },
  hint2: "Look right",
  hint2_i18n: { de: "Schau rechts" },
  tourist_info: "Main street",
  tourist_info_i18n: { de: "Hauptstraße" },
  coordinates: { lat: 59.934, lon: 30.33 },
  task_image_url: null,
  info_image_url: null,
  updated_at: "2024-01-01T00:00:00Z",
};

describe("LandmarksScreen", () => {
  beforeEach(() => {
    vi.mocked(adminApi.landmarks).mockResolvedValue([landmark]);
    vi.mocked(adminApi.createLandmark).mockReset();
    vi.mocked(adminApi.updateLandmark).mockReset();
    vi.mocked(adminApi.deleteLandmark).mockReset();
    vi.mocked(adminApi.uploadLandmarkPicture).mockReset();
  });

  it("lists landmarks", async () => {
    render(<LandmarksScreen subPath="landmarks" />);
    await waitFor(() => {
      expect(screen.getByText("Nevsky Prospekt")).toBeInTheDocument();
    });
    expect(screen.getByText("(nevsky)")).toBeInTheDocument();
  });

  it("creates a landmark", async () => {
    const user = userEvent.setup();
    vi.mocked(adminApi.createLandmark).mockResolvedValueOnce(landmark);

    render(<LandmarksScreen subPath="landmarks" />);
    await waitFor(() => screen.getByText("Nevsky Prospekt"));

    await user.click(screen.getByRole("button", { name: "New landmark" }));
    await user.type(screen.getByLabelText("Key"), "new-key");
    await user.type(screen.getByLabelText("Name"), "New Landmark");
    await user.type(screen.getByLabelText("Task"), "Task text");
    await user.type(screen.getByLabelText("Latitude"), "59.9");
    await user.type(screen.getByLabelText("Longitude"), "30.3");
    await user.click(screen.getByRole("button", { name: "Create landmark" }));

    await waitFor(() => {
      expect(adminApi.createLandmark).toHaveBeenCalled();
    });
    const args = vi.mocked(adminApi.createLandmark).mock.calls[0];
    expect(args[0].key).toBe("new-key");
    expect(args[0].coordinates).toEqual({ lat: 59.9, lon: 30.3 });
  });

  it("updates a landmark with seen_at", async () => {
    const user = userEvent.setup();
    vi.mocked(adminApi.updateLandmark).mockResolvedValueOnce(landmark);

    render(<LandmarksScreen subPath="landmarks" />);
    await waitFor(() => screen.getByText("Nevsky Prospekt"));

    await user.click(screen.getByRole("button", { name: "Edit" }));
    await user.clear(screen.getByLabelText("Name"));
    await user.type(screen.getByLabelText("Name"), "Updated Landmark");
    await user.click(screen.getByRole("button", { name: "Update landmark" }));

    await waitFor(() => {
      expect(adminApi.updateLandmark).toHaveBeenCalledWith(
        1,
        expect.objectContaining({ name: "Updated Landmark", seen_at: "2024-01-01T00:00:00Z" }),
      );
    });
  });

  it("validates hint2 requires hint1", async () => {
    const user = userEvent.setup();
    render(<LandmarksScreen subPath="landmarks" />);
    await waitFor(() => screen.getByText("Nevsky Prospekt"));

    await user.click(screen.getByRole("button", { name: "New landmark" }));
    await user.type(screen.getByLabelText("Key"), "new-key");
    await user.type(screen.getByLabelText("Name"), "New Landmark");
    await user.type(screen.getByLabelText("Task"), "Task text");
    await user.type(screen.getByLabelText("Hint 2"), "no hint1");
    await user.click(screen.getByRole("button", { name: "Create landmark" }));

    expect(await screen.findByText(/Hint 2 requires Hint 1/)).toBeInTheDocument();
    expect(adminApi.createLandmark).not.toHaveBeenCalled();
  });

  it("validates lat/lon are numeric and surfaces field errors", async () => {
    const user = userEvent.setup();
    render(<LandmarksScreen subPath="landmarks" />);
    await waitFor(() => screen.getByText("Nevsky Prospekt"));

    await user.click(screen.getByRole("button", { name: "New landmark" }));
    await user.type(screen.getByLabelText("Key"), "new-key");
    await user.type(screen.getByLabelText("Name"), "New Landmark");
    await user.type(screen.getByLabelText("Task"), "Task text");
    await user.type(screen.getByLabelText("Latitude"), "abc");
    await user.type(screen.getByLabelText("Longitude"), "30.3");
    await user.click(screen.getByRole("button", { name: "Create landmark" }));

    expect(await screen.findByText(/Latitude must be a number/)).toBeInTheDocument();
    expect(adminApi.createLandmark).not.toHaveBeenCalled();
  });

  it("validates partial coordinates are numeric", async () => {
    const user = userEvent.setup();
    render(<LandmarksScreen subPath="landmarks" />);
    await waitFor(() => screen.getByText("Nevsky Prospekt"));

    await user.click(screen.getByRole("button", { name: "New landmark" }));
    await user.type(screen.getByLabelText("Key"), "new-key");
    await user.type(screen.getByLabelText("Name"), "New Landmark");
    await user.type(screen.getByLabelText("Task"), "Task text");
    await user.type(screen.getByLabelText("Latitude"), "59.9");
    await user.type(screen.getByLabelText("Longitude"), "not-a-number");
    await user.click(screen.getByRole("button", { name: "Create landmark" }));

    expect(await screen.findByText(/Longitude must be a number/)).toBeInTheDocument();
    expect(adminApi.createLandmark).not.toHaveBeenCalled();
  });

  it("deletes a landmark after confirmation", async () => {
    const user = userEvent.setup();
    vi.mocked(adminApi.deleteLandmark).mockResolvedValueOnce({ deleted: true });

    render(<LandmarksScreen subPath="landmarks" />);
    await waitFor(() => screen.getByText("Nevsky Prospekt"));

    await user.click(screen.getByRole("button", { name: "Delete" }));
    const confirmButtons = screen.getAllByRole("button", { name: "Delete" });
    await user.click(confirmButtons[confirmButtons.length - 1]);

    await waitFor(() => {
      expect(adminApi.deleteLandmark).toHaveBeenCalledWith(1, false);
    });
  });

  it("offers a force-delete confirmation when the landmark is used by a game", async () => {
    const user = userEvent.setup();
    vi.mocked(adminApi.deleteLandmark)
      .mockRejectedValueOnce(new HttpErrorWithBody(409, { used_by_games: [42] }))
      .mockResolvedValueOnce({ deleted: true });

    render(<LandmarksScreen subPath="landmarks" />);
    await waitFor(() => screen.getByText("Nevsky Prospekt"));

    await user.click(screen.getByRole("button", { name: "Delete" }));
    const confirmButtons = screen.getAllByRole("button", { name: "Delete" });
    await user.click(confirmButtons[confirmButtons.length - 1]);

    await waitFor(() => {
      expect(adminApi.deleteLandmark).toHaveBeenCalledWith(1, false);
    });
    expect(screen.getByText(/used by one or more games/)).toBeInTheDocument();

    await user.click(screen.getByRole("button", { name: "Force delete" }));

    await waitFor(() => {
      expect(adminApi.deleteLandmark).toHaveBeenCalledWith(1, true);
    });
  });

  it("shows a server error when a landmark is blocked by an active or finished run", async () => {
    const user = userEvent.setup();
    vi.mocked(adminApi.deleteLandmark).mockRejectedValueOnce(
      new HttpErrorWithBody(409, { detail: "cannot delete a landmark used by a finished or active run" }),
    );

    render(<LandmarksScreen subPath="landmarks" />);
    await waitFor(() => screen.getByText("Nevsky Prospekt"));

    await user.click(screen.getByRole("button", { name: "Delete" }));
    const confirmButtons = screen.getAllByRole("button", { name: "Delete" });
    await user.click(confirmButtons[confirmButtons.length - 1]);

    await waitFor(() => {
      expect(screen.getByText(/finished or active run/)).toBeInTheDocument();
    });
    expect(adminApi.deleteLandmark).toHaveBeenCalledWith(1, false);
  });

  it("warns before closing when form is dirty", async () => {
    const user = userEvent.setup();
    render(<LandmarksScreen subPath="landmarks" />);
    await waitFor(() => screen.getByText("Nevsky Prospekt"));

    await user.click(screen.getByRole("button", { name: "New landmark" }));
    await user.type(screen.getByLabelText("Name"), "Changed");

    const event = new Event("beforeunload", { cancelable: true });
    window.dispatchEvent(event);
    expect(event.defaultPrevented).toBe(true);
  });

  it("creates a landmark with translations", async () => {
    const user = userEvent.setup();
    vi.mocked(adminApi.createLandmark).mockResolvedValueOnce(landmark);
    vi.stubGlobal("prompt", vi.fn(() => "sr"));

    render(<LandmarksScreen subPath="landmarks" />);
    await waitFor(() => screen.getByText("Nevsky Prospekt"));

    await user.click(screen.getByRole("button", { name: "New landmark" }));
    await user.type(screen.getByLabelText("Key"), "new-key");
    await user.type(screen.getByLabelText("Name"), "New Landmark");
    await user.type(screen.getByLabelText("Task"), "Task text");
    await user.click(screen.getByRole("button", { name: "+ Add language" }));
    await user.type(screen.getByPlaceholderText("Name (sr)"), "Srpski naziv");
    await user.type(screen.getByPlaceholderText("Task (sr)"), "Srpski zadatak");
    await user.click(screen.getByRole("button", { name: "Create landmark" }));

    await waitFor(() => {
      expect(adminApi.createLandmark).toHaveBeenCalled();
    });
    const args = vi.mocked(adminApi.createLandmark).mock.calls[0];
    expect(args[0].name_i18n).toEqual({ sr: "Srpski naziv" });
    expect(args[0].task_i18n).toEqual({ sr: "Srpski zadatak" });

    vi.unstubAllGlobals();
  });

  it("strips blank translation entries before saving", async () => {
    const user = userEvent.setup();
    vi.mocked(adminApi.createLandmark).mockResolvedValueOnce(landmark);
    vi.stubGlobal("prompt", vi.fn(() => "de"));

    render(<LandmarksScreen subPath="landmarks" />);
    await waitFor(() => screen.getByText("Nevsky Prospekt"));

    await user.click(screen.getByRole("button", { name: "New landmark" }));
    await user.type(screen.getByLabelText("Key"), "new-key");
    await user.type(screen.getByLabelText("Name"), "New Landmark");
    await user.type(screen.getByLabelText("Task"), "Task text");
    await user.click(screen.getByRole("button", { name: "+ Add language" }));
    await user.type(screen.getByPlaceholderText("Name (de)"), "German name");
    await user.clear(screen.getByPlaceholderText("Name (de)"));
    await user.click(screen.getByRole("button", { name: "Create landmark" }));

    await waitFor(() => {
      expect(adminApi.createLandmark).toHaveBeenCalled();
    });
    const args = vi.mocked(adminApi.createLandmark).mock.calls[0];
    expect(args[0].name_i18n).toEqual({});

    vi.unstubAllGlobals();
  });

  it("uploads a picture", async () => {
    const user = userEvent.setup();
    vi.mocked(adminApi.uploadLandmarkPicture).mockResolvedValueOnce({
      blob_name: "x.jpg",
      url: "http://test/x.jpg",
    });

    render(<LandmarksScreen subPath="landmarks" />);
    await waitFor(() => screen.getByText("Nevsky Prospekt"));

    await user.click(screen.getByRole("button", { name: "Edit" }));

    const file = new File(["data"], "pic.jpg", { type: "image/jpeg" });
    const input = screen.getByLabelText("Task picture");
    await user.upload(input, file);

    await waitFor(() => {
      expect(adminApi.uploadLandmarkPicture).toHaveBeenCalledWith(1, "task", file);
    });
  });
});
