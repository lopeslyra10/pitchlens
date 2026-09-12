/** Ponto no campo, em metros: `[x, y]`, no mesmo referencial de `pitchlens.pitch` (Python). */
export type Vec2 = readonly [number, number];

export function lerp(a: number, b: number, t: number): number {
  return a + (b - a) * t;
}

export function lerpVec(a: Vec2, b: Vec2, t: number): Vec2 {
  return [lerp(a[0], b[0], t), lerp(a[1], b[1], t)];
}

export function easeInOutCubic(t: number): number {
  return t < 0.5 ? 4 * t ** 3 : 1 - (-2 * t + 2) ** 3 / 2;
}

export function mean(values: readonly number[]): number {
  return values.reduce((sum, value) => sum + value, 0) / values.length;
}

function cross(o: Vec2, a: Vec2, b: Vec2): number {
  return (a[0] - o[0]) * (b[1] - o[1]) - (a[1] - o[1]) * (b[0] - o[0]);
}

/** Casco convexo pelo algoritmo monotone chain de Andrew, sem repetir o primeiro ponto. */
export function convexHull(points: readonly Vec2[]): Vec2[] {
  if (points.length < 3) return [...points];
  const sorted = [...points].sort((a, b) => a[0] - b[0] || a[1] - b[1]);
  const halfHull = (input: readonly Vec2[]) => {
    const chain: Vec2[] = [];
    for (const point of input) {
      while (chain.length >= 2 && cross(chain[chain.length - 2], chain[chain.length - 1], point) <= 0) {
        chain.pop();
      }
      chain.push(point);
    }
    chain.pop();
    return chain;
  };
  return [...halfHull(sorted), ...halfHull([...sorted].reverse())];
}

/** Área de um polígono simples pela fórmula do cadarço (shoelace). */
export function polygonArea(polygon: readonly Vec2[]): number {
  let twiceArea = 0;
  polygon.forEach(([x1, y1], i) => {
    const [x2, y2] = polygon[(i + 1) % polygon.length];
    twiceArea += x1 * y2 - x2 * y1;
  });
  return Math.abs(twiceArea) / 2;
}
