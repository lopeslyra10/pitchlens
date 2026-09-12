import { convexHull, polygonArea, type Vec2 } from "./geometry";

/** Medidas coletivas de um time, em metros; base das métricas da Fase 4. */
export interface TeamShape {
  /** Distância entre os jogadores mais abertos, no sentido da largura do campo. */
  width: number;
  /** Distância entre o jogador mais recuado e o mais avançado. */
  depth: number;
  /** Área (m²) do casco convexo formado pelos jogadores de linha. */
  area: number;
}

export function teamShape(players: readonly Vec2[]): TeamShape {
  if (players.length === 0) return { width: 0, depth: 0, area: 0 };
  const xs = players.map(([x]) => x);
  const ys = players.map(([, y]) => y);
  return {
    width: Math.max(...ys) - Math.min(...ys),
    depth: Math.max(...xs) - Math.min(...xs),
    area: polygonArea(convexHull(players)),
  };
}
