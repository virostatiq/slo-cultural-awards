// Internal links under the site's base path (astro.config base, from SITE_BASE at build;
// "/" in development). Kept separate from data.ts so client scripts can use it without
// bundling the site data.
export const BASE = import.meta.env.BASE_URL.replace(/\/$/, "");
export const url = (path: string) => BASE + path;
