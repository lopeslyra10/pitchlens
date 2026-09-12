import { describe, expect, it } from "vitest";
import { FORMATIONS, OPPONENT_SHAPE, SLOT_NUMBERS } from "./formations";
import { PITCH } from "./pitch";

const insidePitch = ([x, y]: readonly [number, number]) =>
  x >= 0 && x <= PITCH.length && y >= 0 && y <= PITCH.width;

describe("FORMATIONS", () => {
  it.each([...FORMATIONS])("$name: tamanho das linhas bate com o nome", (formation) => {
    expect(formation.lines.map((line) => line.length).join("-")).toBe(formation.name);
  });

  it.each([...FORMATIONS])("$name: usa cada um dos 10 slots exatamente uma vez", (formation) => {
    expect(formation.slots).toHaveLength(SLOT_NUMBERS.length);
    expect(formation.lines.flat().sort((a, b) => a - b)).toEqual([0, 1, 2, 3, 4, 5, 6, 7, 8, 9]);
  });

  it.each([...FORMATIONS])("$name: posições e portador da bola são válidos", (formation) => {
    expect(formation.slots.every(insidePitch)).toBe(true);
    expect(formation.ball.slot).toBeGreaterThanOrEqual(0);
    expect(formation.ball.slot).toBeLessThan(SLOT_NUMBERS.length);
  });
});

describe("OPPONENT_SHAPE", () => {
  it("tem 10 jogadores de linha dentro do campo", () => {
    expect(OPPONENT_SHAPE).toHaveLength(10);
    expect(OPPONENT_SHAPE.every(insidePitch)).toBe(true);
  });
});
