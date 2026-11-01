import { defineConfig } from "astro/config";

// Absolute URLs (canonical, Open Graph) need the public origin: set SITE_URL at build.
// A site served from a subfolder sets SITE_BASE (e.g. /kulturne-nagrade); every internal
// link goes through src/lib/url.ts, so the same code works at "/" in development.
export default defineConfig({
  site: process.env.SITE_URL || "https://kulturne-nagrade.example",
  base: process.env.SITE_BASE || "/",
  trailingSlash: "always",
  build: { format: "directory" },
  vite: { build: { chunkSizeWarningLimit: 2000, target: "es2022" } },
});
