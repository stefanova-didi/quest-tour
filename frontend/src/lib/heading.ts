// Turns DeviceOrientation events into a compass heading.
//
// Browsers disagree about what `alpha` means. Per the W3C spec it grows
// counter-clockwise, so a device pointing east reports alpha 270, not 90. On
// Chrome for Android the plain `deviceorientation` event is also *relative*: zero is
// wherever the phone pointed when the page loaded, and only the separate
// `deviceorientationabsolute` event is referenced to north. Safari never marks an
// event absolute at all; it carries the true clockwise heading in the non-standard
// `webkitCompassHeading` field instead. Using `alpha` directly therefore mirrors the
// arrow on Android and points it at random on iOS.

export type OrientationReading = {
  alpha: number | null;
  absolute?: boolean;
  webkitCompassHeading?: number | null;
};

export function normalizeDegrees(degrees: number): number {
  return ((degrees % 360) + 360) % 360;
}

/**
 * Clockwise heading (0 = north) of the top of the screen, or null when the event
 * cannot tell (relative readings, missing sensor).
 *
 * `screenAngle` is the display rotation from `screen.orientation.angle`, so a phone
 * held in landscape still reports the direction the user is facing.
 */
export function headingFromOrientation(e: OrientationReading, screenAngle = 0): number | null {
  const ios = e.webkitCompassHeading;
  if (typeof ios === "number" && Number.isFinite(ios)) {
    return normalizeDegrees(ios + screenAngle);
  }
  if (e.alpha == null || !Number.isFinite(e.alpha) || !e.absolute) return null;
  return normalizeDegrees(360 - e.alpha + screenAngle);
}

/** Current display rotation in degrees; falls back to the legacy iOS `window.orientation`. */
export function screenAngle(): number {
  const modern = window.screen?.orientation?.angle;
  if (typeof modern === "number") return modern;
  const legacy = (window as { orientation?: unknown }).orientation;
  return typeof legacy === "number" ? legacy : 0;
}

/**
 * Picks the representation of `target` (mod 360) nearest to `previous`, so a CSS
 * `transform` transition turns the short way instead of spinning almost a full
 * circle when the angle crosses 0/360.
 */
export function unwrapRotation(previous: number, target: number): number {
  const delta = normalizeDegrees(target - previous);
  return previous + (delta > 180 ? delta - 360 : delta);
}
