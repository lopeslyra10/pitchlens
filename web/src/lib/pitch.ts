import type { Vec2 } from "./geometry";

/** Dimensões do campo em metros; espelham `PitchSpec` do núcleo Python (`src/pitchlens/pitch.py`). */
export const PITCH = {
  length: 105,
  width: 68,
  penaltyAreaDepth: 16.5,
  penaltyAreaWidth: 40.32,
  goalAreaDepth: 5.5,
  goalAreaWidth: 18.32,
  penaltySpotDistance: 11,
  centerCircleRadius: 9.15,
  goalWidth: 7.32,
} as const;

/** Gira 180° em torno do centro: leva quem ataca para a direita a atacar para a esquerda. */
export function rotateHalfTurn([x, y]: Vec2): Vec2 {
  return [PITCH.length - x, PITCH.width - y];
}
