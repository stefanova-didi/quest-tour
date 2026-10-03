import { act, render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { vi } from "vitest";
import { makeState, makeTask, NEVSKY } from "../test/fixtures";
import { CorrectScreen } from "./CorrectScreen";
import { LandmarkScreen } from "./LandmarkScreen";
import { LoadingScreen } from "./LoadingScreen";
import { NotFoundScreen } from "./NotFoundScreen";
import { RevealedScreen } from "./RevealedScreen";

const frame = { header: null, offline: false, notice: null, onNoticeDone: () => {} };

it("LoadingScreen shows the copy and the banner only when offline", () => {
  const { rerender } = render(<LoadingScreen offline={false} />);
  expect(screen.getByText("Loading your quest…")).toBeInTheDocument();
  expect(screen.queryByText("No connection – retrying…")).toBeNull();
  rerender(<LoadingScreen offline />);
  expect(screen.getByText("No connection – retrying…")).toBeInTheDocument();
});

it("CorrectScreen names the landmark and continues to the photo", async () => {
  const onContinue = vi.fn();
  render(<CorrectScreen state={makeState({ task: makeTask({ completion: "answered", landmark: NEVSKY }) })} frame={frame} onContinue={onContinue} />);
  expect(screen.getByText("Correct!")).toBeInTheDocument();
  expect(screen.getByText("Alexander Nevsky Cathedral")).toBeInTheDocument();
  await userEvent.click(screen.getByRole("button", { name: "Take a photo, create a memory" }));
  expect(onContinue).toHaveBeenCalledTimes(1);
});

it("RevealedScreen shows the answer and the charged penalty", async () => {
  const onContinue = vi.fn();
  const task = makeTask({ completion: "revealed", revealed_answer: "Alexander Nevsky Cathedral", reveal_penalty_minutes: 30, landmark: NEVSKY });
  render(<RevealedScreen state={makeState({ task })} frame={frame} onContinue={onContinue} />);
  expect(screen.getByText("The answer")).toBeInTheDocument();
  expect(screen.getByText("Alexander Nevsky Cathedral")).toBeInTheDocument();
  expect(screen.getByText("+30 min added")).toBeInTheDocument();
  expect(screen.getByText("Head there now – a team photo at Alexander Nevsky Cathedral unlocks the next riddle.")).toBeInTheDocument();
  await userEvent.click(screen.getByRole("button", { name: /Continue/ }));
  expect(onContinue).toHaveBeenCalledTimes(1);
});

it("LandmarkScreen offers the next riddle and disables itself while busy", async () => {
  let release!: () => void;
  const onNext = vi.fn(() => new Promise<"ok">((resolve) => { release = () => resolve("ok"); }));
  const task = makeTask({ completion: "answered", landmark: NEVSKY, photo_count: 1, picture_url: null });
  const { container } = render(<LandmarkScreen state={makeState({ phase: "info", task })} frame={frame} onNext={onNext} />);
  expect(screen.getByText("Landmark 3 of 8")).toBeInTheDocument();
  expect(container.querySelector("img")).toBeNull();
  const button = screen.getByRole("button", { name: /Next riddle/ });
  await userEvent.click(button);
  expect(button).toBeDisabled();
  await act(async () => { release(); });
  await vi.waitFor(() => expect(button).toBeEnabled());
});

it("LandmarkScreen on the last task shows the results card", () => {
  const task = makeTask({ completion: "answered", landmark: { ...NEVSKY, picture_url: "/api/images/n.svg" }, photo_count: 1 });
  render(<LandmarkScreen state={makeState({ phase: "info", position: 7, task })} frame={frame} onNext={vi.fn()} />);
  expect(screen.getByText("That was the last landmark!")).toBeInTheDocument();
  expect(screen.getByRole("button", { name: /See results/ })).toBeInTheDocument();
  expect(screen.getByAltText("Picture of Alexander Nevsky Cathedral")).toBeInTheDocument();
});

it("NotFoundScreen shows the 404 caption only for the default title", () => {
  const { rerender } = render(<NotFoundScreen />);
  expect(screen.getByText("Page not found")).toBeInTheDocument();
  expect(screen.getByText("Error 404")).toBeInTheDocument();
  rerender(<NotFoundScreen title="Open your game link" />);
  expect(screen.getByText("Open your game link")).toBeInTheDocument();
  expect(screen.queryByText("Error 404")).toBeNull();
});
