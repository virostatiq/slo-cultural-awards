import { url } from "./url";
// Client-side: draws the network map as a field of points ("the sky") on a canvas.
// Points come from /data/tocke.json (site_export.map_points): [x, y, field index, is award].
// Used as the home-page backdrop and, dimmed, behind a person with their ties.

type Points = { fields: string[]; points: [number, number, number, number][] };
export type SkyOptions = {
  colors: Record<string, string>;
  fit?: number;            // share of the canvas width the map may use (0–1)
  centerX?: number;        // horizontal centre of the map, as a share of the width
  dim?: boolean;           // fade every point (the person view)
  me?: [number, number] | null;       // highlighted point
  ties?: [number, number][];          // points linked to `me`
};

let cache: Promise<Points> | null = null;
export const loadPoints = () => (cache ??= fetch(url("/data/tocke.json")).then((r) => r.json()));

export function drawSky(cv: HTMLCanvasElement, data: Points, o: SkyOptions) {
  const rect = cv.getBoundingClientRect(), dpr = window.devicePixelRatio || 1;
  if (!rect.width || !rect.height) return;
  cv.width = Math.round(rect.width * dpr); cv.height = Math.round(rect.height * dpr);
  const g = cv.getContext("2d")!;
  g.setTransform(dpr, 0, 0, dpr, 0, 0);
  let x0 = Infinity, x1 = -Infinity, y0 = Infinity, y1 = -Infinity;
  for (const [x, y] of data.points) { x0 = Math.min(x0, x); x1 = Math.max(x1, x); y0 = Math.min(y0, y); y1 = Math.max(y1, y); }
  const W = rect.width, H = rect.height, pad = 16, fit = o.fit ?? 1;
  const s = Math.min((W * fit - pad * 2) / (x1 - x0), (H - pad * 2) / (y1 - y0));
  const ox = W * (o.centerX ?? .5) - ((x0 + x1) / 2) * s, oy = H / 2 + ((y0 + y1) / 2) * s;
  const P = (x: number, y: number) => [ox + x * s, oy - y * s];
  const r = Math.max(.8, Math.min(1.4, s * .9));
  const col = data.fields.map((f) => o.colors[f] ?? "#888");
  g.globalCompositeOperation = "lighter";
  for (const [x, y, f, award] of data.points) {
    const [px, py] = P(x, y);
    g.fillStyle = col[f];
    g.globalAlpha = o.dim ? .14 : award ? .95 : .55;
    g.beginPath(); g.arc(px, py, award ? r * 2.3 : r, 0, 7); g.fill();
  }
  if (o.me) {
    const [mx, my] = P(o.me[0], o.me[1]);
    g.globalCompositeOperation = "source-over";
    g.strokeStyle = "#efe9f4"; g.lineWidth = .6; g.globalAlpha = .3;
    for (const [x, y] of o.ties ?? []) { const [px, py] = P(x, y); g.beginPath(); g.moveTo(mx, my); g.lineTo(px, py); g.stroke(); }
    g.globalAlpha = .9; g.fillStyle = "#efe9f4";
    for (const [x, y] of o.ties ?? []) { const [px, py] = P(x, y); g.beginPath(); g.arc(px, py, 1.6, 0, 7); g.fill(); }
    g.globalAlpha = 1; g.beginPath(); g.arc(mx, my, 4.5, 0, 7); g.fill();
    g.globalAlpha = .25; g.beginPath(); g.arc(mx, my, 10, 0, 7); g.fill();
  }
}

// Draw now and again on resize (debounced); returns nothing, failures leave an empty canvas.
export function mountSky(cv: HTMLCanvasElement, opts: () => SkyOptions) {
  loadPoints().then((data) => {
    const run = () => drawSky(cv, data, opts());
    run();
    let t: number | undefined;
    window.addEventListener("resize", () => { clearTimeout(t); t = window.setTimeout(run, 120); });
  }).catch(() => {});
}
