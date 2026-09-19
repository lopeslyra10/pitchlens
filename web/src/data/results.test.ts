import { existsSync } from "node:fs";
import { fileURLToPath } from "node:url";
import { describe, expect, it } from "vitest";
import { PHASES } from "./roadmap";
import { RESULTS } from "./results";

const publicFile = (path: string) => fileURLToPath(new URL(`../../public/${path}`, import.meta.url));

describe("RESULTS", () => {
  it.each([...RESULTS])("fase $phase: mídia existe na pasta public", (result) => {
    expect(existsSync(publicFile(result.media.src))).toBe(true);
    if (result.media.poster) expect(existsSync(publicFile(result.media.poster))).toBe(true);
  });

  it.each([...RESULTS])("fase $phase: tem texto alternativo, crédito e licença", (result) => {
    expect(result.media.alt.length).toBeGreaterThan(20);
    expect(result.credit.href).toMatch(/^https:\/\//);
    expect(result.credit.license).not.toBe("");
  });

  it("só mostra resultados de fases já iniciadas", () => {
    const started = new Set(PHASES.filter((p) => p.status !== "planned").map((p) => p.id));
    expect(RESULTS.every((result) => started.has(result.phase))).toBe(true);
  });
});
