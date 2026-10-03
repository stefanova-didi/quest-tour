import { paragraphs } from "../lib/format";

export function Paragraphs({ text, className = "t-body" }: { text: string; className?: string }) {
  return <>{paragraphs(text).map((p, i) => <p className={className} key={i}>{p}</p>)}</>;
}
