import { describe, expect, it } from "vitest";
import { FORMATIONS } from "./formations";
import { HOLD_SECONDS, MOVE_SECONDS, boardStateAt } from "./simulation";

const STEP = HOLD_SECONDS + MOVE_SECONDS;

describe("boardStateAt", () => {
  it("começa na primeira formação, com 11 jogadores por time", () => {
    const state = boardStateAt(0);

    expect(state.formation.name).toBe(FORMATIONS[0].name);
    expect(state.home).toHaveLength(11);
    expect(state.away).toHaveLength(11);
    expect(state.lineOpacity).toBe(1);
  });

  it("calcula a linha defensiva a partir das posições da formação", () => {
    const defenders = FORMATIONS[0].lines[0].map((slot) => FORMATIONS[0].slots[slot][0]);
    const expected = defenders.reduce((sum, x) => sum + x, 0) / defenders.length;

    expect(boardStateAt(0).defensiveLine).toBeCloseTo(expected);
  });

  it("esconde as linhas no meio da transição e chega à formação seguinte", () => {
    expect(boardStateAt(HOLD_SECONDS + MOVE_SECONDS / 2).lineOpacity).toBeCloseTo(0);
    expect(boardStateAt(STEP).formation.name).toBe(FORMATIONS[1].name);
  });

  it("volta ao início depois de percorrer todas as formações", () => {
    expect(boardStateAt(STEP * FORMATIONS.length + 0.1).formation.name).toBe(FORMATIONS[0].name);
  });
});
