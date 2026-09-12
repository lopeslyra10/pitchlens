export interface PipelineStep {
  title: string;
  description: string;
  tech: string;
  /** Fase do roadmap em que a etapa é construída. */
  phase: number;
}

export const PIPELINE: readonly PipelineStep[] = [
  {
    title: "Detecção",
    description: "Encontra jogadores, goleiros, árbitros e a bola em cada frame.",
    tech: "RF-DETR ajustado",
    phase: 1,
  },
  {
    title: "Rastreamento",
    description: "Mantém o mesmo identificador para cada jogador ao longo do vídeo.",
    tech: "ByteTrack",
    phase: 2,
  },
  {
    title: "Separação de times",
    description: "Agrupa os jogadores pela aparência do uniforme, sem rótulos manuais.",
    tech: "Embeddings + clustering",
    phase: 2,
  },
  {
    title: "Calibração do campo",
    description: "Localiza pontos do gramado e estima a homografia de cada frame.",
    tech: "Keypoints + OpenCV",
    phase: 3,
  },
  {
    title: "Projeção",
    description: "Converte pixels da câmera em posições reais, em metros, no campo de 105 × 68 m.",
    tech: "Homografia",
    phase: 3,
  },
  {
    title: "Leitura tática",
    description: "Formação por janela com confiança, linhas, largura, profundidade e compactação.",
    tech: "NumPy + algoritmo húngaro",
    phase: 4,
  },
  {
    title: "Mesa tática",
    description: "Vídeo e campo 2D sincronizados, com linha do tempo e métricas.",
    tech: "React + SVG/Canvas",
    phase: 5,
  },
];
