import {
  FORMATIONS,
  HOME_GOALKEEPER,
  OPPONENT_GOALKEEPER,
  OPPONENT_SHAPE,
  SLOT_NUMBERS,
  type Formation,
} from "./formations";
import { convexHull, easeInOutCubic, lerp, lerpVec, mean, type Vec2 } from "./geometry";
import { rotateHalfTurn } from "./pitch";
import { teamShape, type TeamShape } from "./shape";

/** Tempo parado em cada formação e tempo de transição para a seguinte, em segundos. */
export const HOLD_SECONDS = 2.6;
export const MOVE_SECONDS = 1.6;
const STEP_SECONDS = HOLD_SECONDS + MOVE_SECONDS;

export interface BoardPlayer {
  position: Vec2;
  number: number;
  goalkeeper: boolean;
}

export interface BoardState {
  formation: Formation;
  home: BoardPlayer[];
  away: Vec2[];
  ball: Vec2;
  /** Jogadores de cada linha, ordenados no sentido da largura, prontos para desenhar. */
  lines: Vec2[][];
  /** Some no meio da transição, quando o agrupamento em linhas muda. */
  lineOpacity: number;
  hull: Vec2[];
  shape: TeamShape;
  /** Altura média da linha defensiva, em metros a partir do próprio gol. */
  defensiveLine: number;
}

/** Pequena oscilação para os jogadores não parecerem peças paradas. */
function sway([x, y]: Vec2, seed: number, seconds: number): Vec2 {
  return [
    x + 0.7 * Math.sin(seconds * 0.8 + seed * 1.9),
    y + 0.6 * Math.cos(seconds * 0.6 + seed * 2.7),
  ];
}

/** Estado da mesa tática simulada no instante `seconds`. */
export function boardStateAt(seconds: number): BoardState {
  const t = Math.max(0, seconds);
  const index = Math.floor(t / STEP_SECONDS) % FORMATIONS.length;
  const elapsed = t % STEP_SECONDS;
  const progress =
    elapsed < HOLD_SECONDS ? 0 : easeInOutCubic((elapsed - HOLD_SECONDS) / MOVE_SECONDS);
  const from = FORMATIONS[index];
  const to = FORMATIONS[(index + 1) % FORMATIONS.length];
  const current = progress < 0.5 ? from : to;

  // Posições sem oscilação alimentam as métricas (números estáveis); as oscilantes vão para a tela.
  const shapeSlots = from.slots.map((slot, i) => lerpVec(slot, to.slots[i], progress));
  const homeSlots = shapeSlots.map((position, i) => sway(position, i, t));

  const push = lerp(from.opponentPush, to.opponentPush, progress);
  const drift = 3 * Math.sin(t * 0.35);
  const awaySlots = OPPONENT_SHAPE.map(([x, y], i) =>
    sway(rotateHalfTurn([x + push, y + drift]), i + 11, t),
  );

  const defensiveLine = lerp(
    mean(from.lines[0].map((slot) => shapeSlots[slot][0])),
    mean(to.lines[0].map((slot) => shapeSlots[slot][0])),
    progress,
  );

  const ballAt = ({ ball }: Formation): Vec2 => {
    const [x, y] = ball.team === "home" ? homeSlots[ball.slot] : awaySlots[ball.slot];
    return ball.team === "home" ? [x + 1.5, y + 0.8] : [x - 1.5, y - 0.8];
  };

  const goalkeeperX = HOME_GOALKEEPER[0] + Math.max(0, defensiveLine - 24) * 0.18;

  return {
    formation: current,
    home: [
      { position: sway([goalkeeperX, HOME_GOALKEEPER[1]], 10, t), number: 1, goalkeeper: true },
      ...homeSlots.map((position, i) => ({ position, number: SLOT_NUMBERS[i], goalkeeper: false })),
    ],
    away: [sway(rotateHalfTurn(OPPONENT_GOALKEEPER), 21, t), ...awaySlots],
    ball: lerpVec(ballAt(from), ballAt(to), progress),
    lines: current.lines.map((line) =>
      line.map((slot) => homeSlots[slot]).sort((a, b) => a[1] - b[1]),
    ),
    lineOpacity: Math.abs(1 - 2 * progress),
    hull: convexHull(homeSlots),
    shape: teamShape(shapeSlots),
    defensiveLine,
  };
}
