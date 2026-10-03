import { describe, expect, it } from "vitest";
import { formatDateLong, formatDateWeekday, formatHms, formatHours, formatLeft, formatLimit,
         formatPenalty, formatTime, ordinal, paragraphs } from "./format";

describe("format", () => {
  it("formats clocks", () => {
    expect(formatHms(4365)).toBe("01:12:45");
    expect(formatHms(-3)).toBe("00:00:00");
    expect(formatLeft(760)).toBe("12:40 left");
    expect(formatLeft(4365)).toBe("1:12:45 left");
    expect(formatPenalty(25)).toBe("+25 min");
  });
  it("formats durations and ranks", () => {
    expect(formatHours(240)).toBe("4 hours");
    expect(formatHours(60)).toBe("1 hour");
    expect(formatHours(90)).toBe("1 hour 30 minutes");
    expect(formatHours(45)).toBe("45 minutes");
    expect(formatLimit(240)).toBe("4-hour");
    expect(formatLimit(90)).toBe("90-minute");
    expect([1, 2, 3, 4, 11, 12, 13, 21, 22].map(ordinal)).toEqual(
      ["1st", "2nd", "3rd", "4th", "11th", "12th", "13th", "21st", "22nd"]);
  });
  it("formats dates in the game time zone", () => {
    expect(formatDateWeekday("2026-10-10T07:00:00+00:00", "Europe/Sofia")).toBe("Sat, 10 October 2026");
    expect(formatTime("2026-10-10T07:00:00+00:00", "Europe/Sofia")).toBe("10:00");
    expect(formatDateLong("2026-09-14T20:59:59+00:00", "Europe/Sofia")).toBe("14 September 2026");
  });
  it("splits paragraphs on blank lines", () => {
    expect(paragraphs("a\nb\n\n c ")).toEqual(["a\nb", "c"]);
  });
});
