import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { vi } from "vitest";
import type { GameState } from "../api/types";
import { makeState } from "../test/fixtures";
import { WelcomeScreen } from "./WelcomeScreen";

const frame = { header: null, offline: false, notice: null, onNoticeDone: () => {} };

function renderWelcome(overrides: Partial<Omit<Parameters<typeof makeState>[0], "game">> & { game?: Partial<GameState["game"]> } & { onStart?: () => void; onLanguageChange?: (lang: string) => void } = {}) {
  const { onStart = vi.fn(), onLanguageChange = vi.fn(), game: gameOverride, ...stateOverrides } = overrides;
  const base = makeState({ phase: null, status: "not_started", clock: null, task: null, ...stateOverrides });
  const state = gameOverride ? { ...base, game: { ...base.game, ...gameOverride } } : base;
  return render(
    <WelcomeScreen
      state={state}
      frame={frame}
      language="en"
      onLanguageChange={onLanguageChange}
      onStart={onStart}
    />
  );
}

it("lists the rules with the reveal penalty from the game settings", () => {
  renderWelcome();
  expect(screen.getByText("+30 min")).toBeInTheDocument();
  expect(screen.getByText(/You have up to 4 hours\./)).toBeInTheDocument();
  expect(screen.getByText("A city quest in 8 riddles")).toBeInTheDocument();
  expect(screen.getByRole("heading", { name: "Sofia Old Town Quest" })).toBeInTheDocument();
});

it("asks for confirmation before calling onStart", async () => {
  const onStart = vi.fn().mockResolvedValue("ok");
  renderWelcome({ onStart });
  await userEvent.click(screen.getByRole("button", { name: "Start the quest" }));
  expect(screen.getByRole("dialog", { name: "Start the clock?" })).toBeInTheDocument();
  expect(onStart).not.toHaveBeenCalled();
  await userEvent.click(screen.getByRole("button", { name: "Start" }));
  expect(onStart).toHaveBeenCalledTimes(1);
});

it("renders a language toggle for the game's available languages", () => {
  renderWelcome({ game: { available_languages: ["de", "sr"] } });
  expect(screen.getByRole("group", { name: "Language" })).toBeInTheDocument();
  expect(screen.getByRole("button", { name: "Base / EN" })).toBeInTheDocument();
  expect(screen.getByRole("button", { name: "DE" })).toBeInTheDocument();
  expect(screen.getByRole("button", { name: "SR" })).toBeInTheDocument();
});

it("calls onLanguageChange when a language button is clicked", async () => {
  const onLanguageChange = vi.fn();
  renderWelcome({ game: { available_languages: ["de", "sr"] }, onLanguageChange });
  await userEvent.click(screen.getByRole("button", { name: "SR" }));
  expect(onLanguageChange).toHaveBeenCalledWith("sr");
});
