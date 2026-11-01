import { defineCollection, z } from "astro:content";
import { glob } from "astro/loaders";

// Findings (/ugotovitve/): Slovenian text with {{key}} placeholders. The numbers and the
// chart come from src/data/findings.json (kulturne_nagrade.site_findings), keyed by the
// file name, so the text follows the analyses on every re-run.
const ugotovitve = defineCollection({
  loader: glob({ pattern: "*.md", base: "./src/content/ugotovitve" }),
  schema: z.object({
    title: z.string(),          // the finding, as a plain sentence
    lede: z.string(),           // one or two sentences; also the page description
    order: z.number(),
    chartTitle: z.string(),
    chartNote: z.string().optional(),   // under the chart: what is counted, caveats
    method: z.string(),         // "Kako smo merili", plain words
    awards: z.array(z.string()).default([]),
  }),
});

export const collections = { ugotovitve };
