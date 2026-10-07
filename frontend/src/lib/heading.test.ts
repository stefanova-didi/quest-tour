import { afterEach, describe, expect, it } from "vitest";
import { headingFromOrientation, normalizeDegrees, screenAngle, unwrapRotation } from "./heading";

describe("headingFromOrientation", () => {
  it("converts an absolute W3C alpha (counter-clockwise) to a clockwise heading", () => {
    expect(headingFromOrientation({ alpha: 0, absolute: true })).toBe(0);
    expect(headingFromOrientation({ alpha: 270, absolute: true })).toBe(90); // facing east
    expect(headingFromOrientation({ alpha: 90, absolute: true })).toBe(270); // facing west
    expect(headingFromOrientation({ alpha: 180, absolute: true })).toBe(180);
  });

  it("ignores relative alpha readings, which are not referenced to north", () => {
    expect(headingFromOrientation({ alpha: 90, absolute: false })).toBeNull();
    expect(headingFromOrientation({ alpha: 90 })).toBeNull();
  });

  it("returns null without any usable angle", () => {
    expect(headingFromOrientation({ alpha: null, absolute: true })).toBeNull();
    expect(headingFromOrientation({ alpha: NaN, absolute: true })).toBeNull();
    expect(headingFromOrientation({ alpha: null, webkitCompassHeading: null })).toBeNull();
  });

  it("prefers Safari's webkitCompassHeading, which is already clockwise", () => {
    expect(headingFromOrientation({ alpha: 123, absolute: false, webkitCompassHeading: 90 })).toBe(90);
    expect(headingFromOrientation({ alpha: 0, webkitCompassHeading: 359.5 })).toBe(359.5);
  });

  it("adds the screen rotation so landscape still reports where the user faces", () => {
    expect(headingFromOrientation({ alpha: 0, absolute: true }, 90)).toBe(90);
    expect(headingFromOrientation({ alpha: 0, absolute: true }, 270)).toBe(270);
    expect(headingFromOrientation({ alpha: 0, absolute: true }, -90)).toBe(270);
    expect(headingFromOrientation({ alpha: 0, webkitCompassHeading: 350 }, 90)).toBe(80);
  });
});

describe("normalizeDegrees", () => {
  it("maps any angle into [0, 360)", () => {
    expect(normalizeDegrees(360)).toBe(0);
    expect(normalizeDegrees(-90)).toBe(270);
    expect(normalizeDegrees(725)).toBe(5);
  });
});

describe("unwrapRotation", () => {
  it("takes the short way round across the 0/360 seam", () => {
    expect(unwrapRotation(350, 10)).toBe(370);
    expect(unwrapRotation(10, 350)).toBe(-10);
    expect(unwrapRotation(370, 20)).toBe(380);
  });

  it("leaves small moves alone", () => {
    expect(unwrapRotation(90, 100)).toBe(100);
    expect(unwrapRotation(100, 90)).toBe(90);
    expect(unwrapRotation(0, 180)).toBe(180);
  });
});

describe("screenAngle", () => {
  const original = Object.getOwnPropertyDescriptor(window.screen, "orientation");
  afterEach(() => {
    if (original) Object.defineProperty(window.screen, "orientation", original);
    else delete (window.screen as { orientation?: unknown }).orientation;
    delete (window as { orientation?: unknown }).orientation;
  });

  it("reads screen.orientation.angle when present", () => {
    Object.defineProperty(window.screen, "orientation", { value: { angle: 90 }, configurable: true });
    expect(screenAngle()).toBe(90);
  });

  it("falls back to window.orientation, then to 0", () => {
    Object.defineProperty(window.screen, "orientation", { value: undefined, configurable: true });
    (window as { orientation?: number }).orientation = -90;
    expect(screenAngle()).toBe(-90);
    delete (window as { orientation?: unknown }).orientation;
    expect(screenAngle()).toBe(0);
  });
});
