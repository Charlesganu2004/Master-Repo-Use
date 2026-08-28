/**
 * Static contract for the UI design studio.
 *
 * The browser uses design-options.js directly so the gallery has no build or
 * package install requirement. This TypeScript file keeps the content model
 * explicit for editors and the repository checks.
 */

export type StudioMode = "dark" | "light";

export interface Palette {
  [token: string]: string;
  bg: string;
  panel: string;
  panel2: string;
  ink: string;
  ink2: string;
  ink3: string;
  accent: string;
  accent2: string;
  onAccent: string;
  ok: string;
  codeBg: string;
  codeInk: string;
  codeMuted: string;
  r: string;
  rSm: string;
  shadow: string;
  fontDisplay: string;
  fontBody: string;
  fontMono: string;
  texture: string;
}

export interface Design {
  id: string;
  index: string;
  name: string;
  layout: string;
  label: string;
  description: string;
  dark: Palette;
  light: Palette;
}

export const GALLERY_META = {
  release: "V7",
  palette: "Graphite",
  state: "Current",
  componentCount: 52,
  laneCount: 16,
  canvasCount: 12,
  routeCount: 36,
  lensMode: "dim",
  routing: "hybrid",
} as const;

/**
 * The IDs and unique dark accent colors used by the browser runtime.
 * They are intentionally public aggregate design data, never catalog data.
 */
export const DESIGN_OPTIONS = [
  { id: "graphite", name: "V7 Graphite Atlas", accent: "#ff8a3d" },
  { id: "polar", name: "Polar Ledger", accent: "#58d1df" },
  { id: "carbon", name: "Carbon Signal", accent: "#55d6ff" },
  { id: "verdant", name: "Verdant Archive", accent: "#9bd09d" },
  { id: "cobalt", name: "Cobalt Blueprint", accent: "#ffd45a" },
  { id: "coral", name: "Coral Workshop", accent: "#ffbd64" },
  { id: "plum", name: "Plum Observatory", accent: "#e5a3ff" },
  { id: "ink", name: "Ink Newsroom", accent: "#ff9b8e" },
  { id: "citrus", name: "Citrus Grid", accent: "#c6ef55" },
  { id: "phosphor", name: "Phosphor Desk", accent: "#74e66b" },
  { id: "porcelain", name: "Porcelain Museum", accent: "#d9b277" },
  { id: "azure", name: "Azure Metro", accent: "#67b4ff" },
  { id: "rose", name: "Rose Circuit", accent: "#ffb0c8" },
  { id: "clay", name: "Clay Field Notes", accent: "#e9b96e" },
  { id: "hazard", name: "Hazard Manual", accent: "#ffe35b" },
  { id: "dawn", name: "Dawn Topography", accent: "#c9a6f4" },
  { id: "pixel", name: "Paper Pixel", accent: "#69dfb8" },
  { id: "cinema", name: "Data Cinema", accent: "#f2703c" },
] as const;
