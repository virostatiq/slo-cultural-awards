// Findings: the text (src/content/ugotovitve/*.md) refers to numbers as {{key}}; the
// numbers and chart specs come from src/data/findings.json (kulturne_nagrade.site_findings).
import findingsJson from "../data/findings.json";

export type ChartSpec = { type: "bars" | "lines"; props: Record<string, any> };
export type FindingData = { n: Record<string, string | null>; chart: ChartSpec };
export const findingData = findingsJson as unknown as Record<string, FindingData>;

// Replace {{key}} with the exported number; an unknown key is left visible on purpose,
// so a missing number shows up in review instead of silently disappearing.
export function fill(text: string, n: Record<string, string | null> = {}) {
  return text.replace(/\{\{\s*(\w+)\s*\}\}/g, (m, k) => (n[k] ?? m));
}
import { url } from "./url";
export const findingUrl = (id: string) => url(`/ugotovitve/${id}/`);
