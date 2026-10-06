const RAD = Math.PI / 180;

export function bearing(lat1: number, lon1: number, lat2: number, lon2: number): number {
  const dLon = (lon2 - lon1) * RAD;
  const y = Math.sin(dLon) * Math.cos(lat2 * RAD);
  const x =
    Math.cos(lat1 * RAD) * Math.sin(lat2 * RAD) -
    Math.sin(lat1 * RAD) * Math.cos(lat2 * RAD) * Math.cos(dLon);
  const brng = Math.atan2(y, x) / RAD;
  return (brng + 360) % 360;
}

const WORDS = ["north", "north-east", "east", "south-east", "south", "south-west", "west", "north-west"];

export function bearingWord(degrees: number): string {
  return WORDS[Math.round(degrees / 45) % 8];
}
