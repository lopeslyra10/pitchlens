export interface ResultMetric {
  label: string;
  value: string;
}

export interface ResultMedia {
  kind: "image" | "video";
  /** Caminho relativo à pasta `public/`. */
  src: string;
  /** Quadro exibido antes do vídeo carregar. */
  poster?: string;
  alt: string;
}

export interface ResultCredit {
  text: string;
  href: string;
  license: string;
}

export interface PhaseResult {
  phase: number;
  title: string;
  summary: string;
  media: ResultMedia;
  metrics: readonly ResultMetric[];
  credit: ResultCredit;
  reportUrl: string;
}

const REPORTS = "https://github.com/lopeslyra10/pitchlens/blob/main/reports";

export const RESULTS: readonly PhaseResult[] = [
  {
    phase: 1,
    title: "Detecção",
    summary:
      "RF-DETR ajustado para futebol encontra jogadores, goleiros, árbitros e bola. Comparado com um YOLO pelo mesmo avaliador, detecta melhor a bola.",
    media: {
      kind: "image",
      src: "resultados/fase-01-deteccao.jpg",
      alt: "Jogo noturno filmado do alto de um estádio, com os jogadores detectados e rotulados.",
    },
    metrics: [
      { label: "mAP@50 no teste", value: "0,889" },
      { label: "AP50 da bola", value: "0,646" },
      { label: "YOLO26m (AP50 bola)", value: "0,580" },
    ],
    credit: {
      text: "Vídeo original do Pexels",
      href: "https://www.pexels.com/video/aerial-footage-of-a-game-of-soccer-2657261/",
      license: "Licença Pexels",
    },
    reportUrl: `${REPORTS}/fase-1/README.md`,
  },
  {
    phase: 2,
    title: "Rastreamento e times",
    summary:
      "Cada jogador ganha um número e a cor do próprio time, aprendida do vídeo sem rótulos. Quem não é de nenhum time, como a arbitragem, fica de fora.",
    media: {
      kind: "video",
      src: "resultados/fase-02-rastreamento.mp4",
      poster: "resultados/fase-02-rastreamento.jpg",
      alt: "Jogo feminino com jogadoras de branco e de vermelho marcadas com números e rastros na cor do time.",
    },
    metrics: [
      { label: "Identificadores criados", value: "329 → 78" },
      { label: "Duração mediana do rastro", value: "0,5 s → 3,8 s" },
      { label: "Trocas de time em 111 recortes", value: "0" },
    ],
    credit: {
      text: "Vídeo original de NaBUru38 (Wikimedia Commons); versão anotada sob a mesma licença",
      href: "https://commons.wikimedia.org/wiki/File:2018_FIFA_U-17_Women%27s_World_Cup_-_New_Zealand_vs_Canada_-_25.webm",
      license: "CC BY-SA 4.0",
    },
    reportUrl: `${REPORTS}/fase-2/README.md`,
  },
];
