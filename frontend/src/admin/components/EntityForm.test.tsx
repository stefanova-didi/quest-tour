import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { EntityForm } from "./EntityForm";

type TestEntity = {
  key: string;
  name: string;
  count: number;
  notes: string;
  tags: string[];
};

const fields = [
  { name: "key", label: "Key", type: "text" as const, required: true },
  { name: "name", label: "Name", type: "text" as const },
  { name: "count", label: "Count", type: "number" as const },
  { name: "notes", label: "Notes", type: "textarea" as const },
  { name: "tags", label: "Tags", type: "list" as const },
];

const initial: TestEntity = {
  key: "start",
  name: "Start",
  count: 1,
  notes: "initial note",
  tags: ["a", "b"],
};

describe("EntityForm", () => {
  const onSubmit = vi.fn();
  const onDirtyChange = vi.fn();

  beforeEach(() => {
    onSubmit.mockReset();
    onDirtyChange.mockReset();
  });

  it("renders all field types", () => {
    render(
      <EntityForm
        fields={fields}
        initial={initial}
        onSubmit={onSubmit}
        submitLabel="Save"
      />,
    );

    expect(screen.getByLabelText("Key")).toHaveValue("start");
    expect(screen.getByLabelText("Name")).toHaveValue("Start");
    expect(screen.getByLabelText("Count")).toHaveValue(1);
    expect(screen.getByLabelText("Notes")).toHaveValue("initial note");
    expect(screen.getByRole("button", { name: "Save" })).toBeInTheDocument();
  });

  it("tracks dirty state and calls onDirtyChange", async () => {
    render(
      <EntityForm
        fields={fields}
        initial={initial}
        onSubmit={onSubmit}
        onDirtyChange={onDirtyChange}
      />,
    );

    fireEvent.change(screen.getByLabelText("Name"), { target: { value: "Changed" } });

    await waitFor(() => {
      expect(onDirtyChange).toHaveBeenLastCalledWith(true);
    });

    fireEvent.change(screen.getByLabelText("Name"), { target: { value: "Start" } });

    await waitFor(() => {
      expect(onDirtyChange).toHaveBeenLastCalledWith(false);
    });
  });

  it("submits current values", async () => {
    const user = userEvent.setup();
    render(
      <EntityForm
        fields={fields}
        initial={initial}
        onSubmit={onSubmit}
        submitLabel="Save"
      />,
    );

    await user.clear(screen.getByLabelText("Name"));
    await user.type(screen.getByLabelText("Name"), "New name");
    await user.click(screen.getByRole("button", { name: "Save" }));

    await waitFor(() => {
      expect(onSubmit).toHaveBeenCalledWith(expect.objectContaining({ name: "New name" }));
    });
  });

  it("renders validation errors", () => {
    render(
      <EntityForm
        fields={fields}
        initial={initial}
        onSubmit={onSubmit}
        errors={[
          { field: "key", message: "Key is required" },
          { field: "tags", message: "Too many tags" },
        ]}
      />,
    );

    expect(screen.getByText("Key is required")).toBeInTheDocument();
    expect(screen.getByText("Too many tags")).toBeInTheDocument();
  });

  it("renders inline errors for empty required fields", async () => {
    const user = userEvent.setup();
    render(
      <EntityForm
        fields={[{ name: "key", label: "Key", type: "text" as const, required: true }]}
        initial={{ key: "" }}
        onSubmit={onSubmit}
        submitLabel="Save"
      />,
    );

    await user.click(screen.getByRole("button", { name: "Save" }));

    expect(await screen.findByText("Key is required")).toBeInTheDocument();
    expect(onSubmit).not.toHaveBeenCalled();
  });

  it("submits after required fields are filled", async () => {
    const user = userEvent.setup();
    render(
      <EntityForm
        fields={[{ name: "key", label: "Key", type: "text" as const, required: true }]}
        initial={{ key: "" }}
        onSubmit={onSubmit}
        submitLabel="Save"
      />,
    );

    await user.type(screen.getByLabelText("Key"), "new-key");
    await user.click(screen.getByRole("button", { name: "Save" }));

    await waitFor(() => {
      expect(onSubmit).toHaveBeenCalledWith({ key: "new-key" });
    });
  });

  it("disables the submit button while busy", () => {
    render(
      <EntityForm
        fields={fields}
        initial={initial}
        onSubmit={onSubmit}
        submitLabel="Save"
        busy
      />,
    );

    expect(screen.getByRole("button", { name: "Save" })).toBeDisabled();
  });

  it("supports list add and remove", async () => {
    const user = userEvent.setup();
    render(
      <EntityForm
        fields={[{ name: "tags", label: "Tags", type: "list" }]}
        initial={{ tags: ["a"] }}
        onSubmit={onSubmit}
        submitLabel="Save"
      />,
    );

    await user.click(screen.getByRole("button", { name: "Add Tags" }));
    await waitFor(() => {
      expect(screen.getAllByRole("textbox").length).toBe(2);
    });

    await user.click(screen.getAllByRole("button", { name: "Remove" })[0]);
    await waitFor(() => {
      expect(screen.getAllByRole("textbox").length).toBe(1);
    });
  });
});
