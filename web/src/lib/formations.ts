import type { Vec2 } from "./geometry";

/**
 * Cada formação posiciona os mesmos 10 "slots" (papéis), sempre com o time atacando para a
 * direita. Manter o papel de cada slot faz a transição entre formações parecer movimento real:
 *
 * 0 lateral esquerdo · 1 zagueiro esquerdo · 2 zagueiro direito · 3 lateral direito ·
 * 4 ponta/meia esquerda · 5 meia direito (8) · 6 meia armador (10) · 7 ponta/meia direita ·
 * 8 volante (5) · 9 centroavante.
 */
export const SLOT_NUMBERS = [6, 3, 4, 2, 11, 8, 10, 7, 5, 9] as const;

export type Team = "home" | "away";

export interface Formation {
  /** Nome no formato defesa-meio-ataque, por exemplo "4-3-3". */
  name: string;
  /** Momento do jogo que a formação ilustra. */
  context: string;
  /** Posição de cada slot, em metros. */
  slots: readonly Vec2[];
  /** Slots agrupados por linha, da defesa para o ataque. */
  lines: readonly (readonly number[])[];
  /** Quem está com a bola: time e slot. */
  ball: { team: Team; slot: number };
  /** Quanto o adversário avança neste momento, em metros (negativo = recua). */
  opponentPush: number;
}

export const HOME_GOALKEEPER: Vec2 = [4, 34];

export const FORMATIONS: readonly Formation[] = [
  {
    name: "4-4-2",
    context: "Bloco médio sem a bola",
    slots: [[27, 10], [25, 26], [25, 42], [27, 58], [42, 11], [40, 41], [55, 29], [42, 57], [40, 27], [57, 40]],
    lines: [[0, 1, 2, 3], [4, 8, 5, 7], [6, 9]],
    ball: { team: "away", slot: 5 },
    opponentPush: 12,
  },
  {
    name: "4-1-4-1",
    context: "Saída de bola",
    slots: [[28, 9], [25, 26], [25, 42], [28, 59], [50, 9], [48, 43], [48, 25], [50, 59], [36, 34], [64, 34]],
    lines: [[0, 1, 2, 3], [8], [4, 6, 5, 7], [9]],
    ball: { team: "home", slot: 8 },
    opponentPush: 6,
  },
  {
    name: "4-3-3",
    context: "Progressão pelos corredores",
    slots: [[34, 9], [31, 26], [31, 42], [34, 59], [70, 10], [56, 44], [56, 24], [70, 58], [46, 34], [74, 34]],
    lines: [[0, 1, 2, 3], [6, 8, 5], [4, 9, 7]],
    ball: { team: "home", slot: 4 },
    opponentPush: 0,
  },
  {
    name: "2-3-5",
    context: "Ataque posicional",
    slots: [[54, 19], [40, 24], [40, 44], [54, 49], [78, 6], [76, 45], [76, 23], [78, 62], [52, 34], [82, 34]],
    lines: [[1, 2], [0, 8, 3], [4, 6, 9, 5, 7]],
    ball: { team: "home", slot: 6 },
    opponentPush: -8,
  },
  {
    name: "4-2-3-1",
    context: "Recomposição após a perda",
    slots: [[26, 10], [23, 26], [23, 42], [26, 58], [50, 12], [36, 41], [51, 34], [50, 56], [36, 27], [64, 34]],
    lines: [[0, 1, 2, 3], [8, 5], [4, 6, 7], [9]],
    ball: { team: "away", slot: 9 },
    opponentPush: 14,
  },
];

/** Adversário em 4-4-2 compacto, descrito atacando para a direita (é girado 180° ao desenhar). */
export const OPPONENT_SHAPE: readonly Vec2[] = [
  [26, 11], [24, 27], [24, 41], [26, 57], [40, 12], [39, 42], [52, 30], [40, 56], [39, 26], [53, 39],
];

export const OPPONENT_GOALKEEPER: Vec2 = [4, 34];
