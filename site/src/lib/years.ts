// Editions grouped by year (built from awards.json).
import { awards, type Award, type Edition } from "./data";

export type YearEntry = { award: Award; editions: Edition[] };
export const byYear = new Map<number, YearEntry[]>();
for (const a of Object.values(awards)) {
  const per = new Map<number, Edition[]>();
  for (const e of a.editions) per.set(e.year, [...(per.get(e.year) ?? []), e]);
  for (const [y, eds] of per) byYear.set(y, [...(byYear.get(y) ?? []), { award: a, editions: eds }]);
}
for (const list of byYear.values())
  list.sort((x, y) => y.award.prestige - x.award.prestige || x.award.name.localeCompare(y.award.name, "sl"));
export const years = [...byYear.keys()].sort((a, b) => a - b);
