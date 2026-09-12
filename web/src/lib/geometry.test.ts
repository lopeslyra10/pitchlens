import { describe, expect, it } from "vitest";
import { convexHull, easeInOutCubic, lerpVec, polygonArea } from "./geometry";
import { teamShape } from "./shape";

describe("convexHull", () => {
  it("descarta pontos internos", () => {
    const hull = convexHull([[0, 0], [4, 0], [4, 4], [0, 4], [2, 2], [1, 3]]);

    expect(hull).toHaveLength(4);
    expect(polygonArea(hull)).toBe(16);
  });

  it("devolve conjuntos com menos de três pontos sem alteração", () => {
    expect(convexHull([[1, 1], [2, 2]])).toEqual([[1, 1], [2, 2]]);
  });
});

describe("polygonArea", () => {
  it("calcula a área de um triângulo retângulo", () => {
    expect(polygonArea([[0, 0], [4, 0], [0, 3]])).toBe(6);
  });
});

describe("teamShape", () => {
  it("mede largura, profundidade e área ocupada", () => {
    const shape = teamShape([[10, 10], [30, 10], [30, 50], [10, 50], [20, 30]]);

    expect(shape).toEqual({ width: 40, depth: 20, area: 800 });
  });
});

describe("interpolação", () => {
  it("easeInOutCubic preserva os extremos e o ponto médio", () => {
    expect(easeInOutCubic(0)).toBe(0);
    expect(easeInOutCubic(0.5)).toBe(0.5);
    expect(easeInOutCubic(1)).toBe(1);
  });

  it("lerpVec interpola os dois eixos", () => {
    expect(lerpVec([0, 10], [10, 30], 0.25)).toEqual([2.5, 15]);
  });
});
