import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { vi } from "vitest";
import { NetworkError } from "../api/client";
import { makeState, makeTask, NEVSKY } from "../test/fixtures";
import { PhotoScreen } from "./PhotoScreen";

const frame = { header: null, offline: false, notice: null, onNoticeDone: () => {} };
const photoState = () => makeState({ phase: "photo", task: makeTask({ completion: "answered", landmark: NEVSKY }) });
const savedState = makeState({ phase: "info", task: makeTask({ completion: "answered", landmark: NEVSKY, photo_count: 1 }) });

it("keeps the file across a failed upload, retries it, and never previews it", async () => {
  const createObjectURL = vi.fn();
  URL.createObjectURL = createObjectURL;
  const upload = vi.fn()
    .mockRejectedValueOnce(new NetworkError())
    .mockResolvedValueOnce({ outcome: "ok", state: savedState });
  const onError = vi.fn();
  const onUploaded = vi.fn();
  const { container } = render(<PhotoScreen state={photoState()} frame={frame} upload={upload}
                                            onFlowStart={vi.fn()} onUploaded={onUploaded} onContinue={vi.fn()} onError={onError} />);
  const file = new File([new Uint8Array([0xff, 0xd8, 0xff])], "p.jpg", { type: "image/jpeg" });
  await userEvent.upload(container.querySelectorAll("input[type=file]")[1] as HTMLInputElement, file);
  expect(await screen.findByText("Upload failed – check your connection")).toBeInTheDocument();
  expect(onError).toHaveBeenCalledTimes(1);
  expect(container.querySelector("img")).toBeNull();

  await userEvent.click(screen.getByRole("button", { name: /Retry/ }));
  expect(await screen.findByText("Photo saved ✓")).toBeInTheDocument();
  expect(upload).toHaveBeenCalledTimes(2);
  expect(upload.mock.calls[1][0]).toBe(upload.mock.calls[0][0]);
  expect(upload.mock.calls[0][0]).toBe(file);
  expect(onUploaded).toHaveBeenCalledTimes(1);
  expect(container.querySelector("img")).toBeNull();
  expect(createObjectURL).not.toHaveBeenCalled();
});

it("refuses a photo over 20 MB without uploading it", async () => {
  const upload = vi.fn();
  const { container } = render(<PhotoScreen state={photoState()} frame={frame} upload={upload}
                                            onFlowStart={vi.fn()} onUploaded={vi.fn()} onContinue={vi.fn()} onError={vi.fn()} />);
  const file = new File([new Uint8Array([0xff])], "big.jpg", { type: "image/jpeg" });
  Object.defineProperty(file, "size", { value: 21 * 1024 * 1024 });
  await userEvent.upload(container.querySelectorAll("input[type=file]")[0] as HTMLInputElement, file);
  expect(await screen.findByText("This photo is larger than 20 MB")).toBeInTheDocument();
  expect(upload).not.toHaveBeenCalled();
});

it("locks Continue until a photo is saved", () => {
  render(<PhotoScreen state={photoState()} frame={frame} upload={vi.fn()}
                      onFlowStart={vi.fn()} onUploaded={vi.fn()} onContinue={vi.fn()} onError={vi.fn()} />);
  expect(screen.getByRole("button", { name: /Continue · add a photo first/ })).toBeDisabled();
  expect(screen.getByText("Take a photo of your team at Alexander Nevsky Cathedral.")).toBeInTheDocument();
});

it("starts as saved when a photo already exists and continues", async () => {
  const onContinue = vi.fn();
  render(<PhotoScreen state={makeState({ phase: "photo", task: makeTask({ completion: "answered", landmark: NEVSKY, photo_count: 2 }) })}
                      frame={frame} upload={vi.fn()} onFlowStart={vi.fn()} onUploaded={vi.fn()} onContinue={onContinue} onError={vi.fn()} />);
  expect(screen.getByText("2 photos ready for the album")).toBeInTheDocument();
  await userEvent.click(screen.getByRole("button", { name: /Continue/ }));
  expect(onContinue).toHaveBeenCalledTimes(1);
});
