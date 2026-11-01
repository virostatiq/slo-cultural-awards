// Site data, exported by `npm run data` (kulturne_nagrade.site_export). Read at build.
import peopleJson from "../data/people.json";
import awardsJson from "../data/awards.json";
import metaJson from "../data/meta.json";

export type Life = { year: number; source: string | null; automated: boolean } | null;
export type Win = { year: number; award: string; edition: string; category: string | null };
export type Jury = { year: number; award: string; awards: string[]; edition: string; size: number };
export type Person = {
  id: string; name: string; kind: string; field: string; role: "winner" | "jury" | "both";
  birth: Life; death: Life; wins: Win[]; juries: Jury[];
  co: [string, number][]; judged_by: [string, number][]; judged: [string, number][];
  first: number; last: number; pos: [number, number] | null; sources: string[]; single: boolean;
};
export type Edition = {
  id: string; year: number; category: string | null; winners: string[]; jury: string[];
  jury_known: boolean;
};
type Test = { expected: number; q: number | null } & Record<string, number | null>;
export type Award = {
  id: string; name: string; genre: string; field: string; prestige: number;
  institution: string | null; founded: number | null; ended: number | null;
  description: string | null; editions: Edition[]; top_jurors: [string, number][];
  stats: {
    winners: number; jurors: number; female_share_winners: number | null;
    female_share_jury: number | null; median_age: number | null;
    insider: Test | null; repeat_winners: Test | null;
    repeat_seats: { share: number; seats: number } | null;
    history_share: number | null; data_from: number | null; data_to: number | null;
  };
};

export const people = peopleJson as unknown as Record<string, Person>;
export const awards = awardsJson as unknown as Record<string, Award>;
export const meta = metaJson as unknown as {
  fields: Record<string, string>; roles: Record<string, string>;
  role_labels: Record<string, string>; kind_labels: Record<string, string>;
  counts: { people: number; awards: number; editions: number; wins: number; sittings: number;
            years: [number, number] };
};

import { url } from "./url";
export { url };
export const personUrl = (id: string) => url(`/oseba/${id}/`);
export const awardUrl = (id: string) => url(`/nagrada/${id}/`);
export const yearUrl = (y: number) => url(`/leto/${y}/`);
export const name = (id: string) => people[id]?.name ?? awards[id]?.name ?? id;

const nf = new Intl.NumberFormat("sl-SI");
export const fmt = (n: number) => nf.format(n);
export const dec = (n: number, d = 1) => n.toFixed(d).replace(".", ",").replace("-", "−");
export const pct = (x: number) => `${Math.round(100 * x)} %`;

// Slovenian plural forms: 1 nagrada, 2 nagradi, 3–4 nagrade, 5+ nagrad (and 101, 102, ...)
export function plural(n: number, [one, two, few, many]: [string, string, string, string]) {
  const m = Math.abs(n) % 100;
  return m === 1 ? one : m === 2 ? two : m === 3 || m === 4 ? few : many;
}
export const nAwards = (n: number) => `${fmt(n)} ${plural(n, ["nagrada", "nagradi", "nagrade", "nagrad"])}`;
export const nJuries = (n: number) => `${fmt(n)} ${plural(n, ["žirija", "žiriji", "žirije", "žirij"])}`;
export const nTimes = (n: number) => `${fmt(n)}×`;

export const span = (a: number | null, b: number | null) =>
  a == null ? "" : a === b ? `${a}` : `${a}–${b}`;
