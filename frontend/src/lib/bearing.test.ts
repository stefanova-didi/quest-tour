import { describe, expect, it } from "vitest";
import { bearing, bearingWord } from "./bearing";

describe("bearing", () => {
  it("computes cardinal directions", () => {
    const lat = 42.6977;
    const lon = 23.3219;
    expect(bearing(lat, lon, lat + 1, lon)).toBeCloseTo(0, 0);
    expect(bearing(lat, lon, lat - 1, lon)).toBeCloseTo(180, 0);
    expect(bearing(lat, lon, lat, lon + 1)).toBeCloseTo(90, 0);
    expect(bearing(lat, lon, lat, lon - 1)).toBeCloseTo(270, 0);
  });

  it("computes diagonal directions at the equator", () => {
    // At lat = 0, a 1° change in both latitude and longitude gives exact diagonals.
    expect(bearing(0, 0, 1, 1)).toBeCloseTo(45, 0);
    expect(bearing(0, 0, -1, 1)).toBeCloseTo(135, 0);
    expect(bearing(0, 0, -1, -1)).toBeCloseTo(225, 0);
    expect(bearing(0, 0, 1, -1)).toBeCloseTo(315, 0);
  });

  it("returns a known real-world bearing", () => {
    // Sofia to Plovdiv is roughly south-east.
    expect(bearing(42.6977, 23.3219, 42.1354, 24.7453)).toBeCloseTo(118, 0);
  });
});

describe("bearingWord", () => {
  it("returns cardinals and diagonals", () => {
    expect(bearingWord(0)).toBe("north");
    expect(bearingWord(45)).toBe("north-east");
    expect(bearingWord(90)).toBe("east");
    expect(bearingWord(135)).toBe("south-east");
    expect(bearingWord(180)).toBe("south");
    expect(bearingWord(225)).toBe("south-west");
    expect(bearingWord(270)).toBe("west");
    expect(bearingWord(315)).toBe("north-west");
  });

  it("wraps around 360 degrees", () => {
    expect(bearingWord(360)).toBe("north");
    expect(bearingWord(720)).toBe("north");
  });

  it("rounds to nearest sector", () => {
    expect(bearingWord(22)).toBe("north");
    expect(bearingWord(23)).toBe("north-east");
  });
});
