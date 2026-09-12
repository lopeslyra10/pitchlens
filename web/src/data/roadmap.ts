export type PhaseStatus = "done" | "active" | "next" | "planned";

export interface Phase {
  id: number;
  title: string;
  version: string;
  status: PhaseStatus;
  summary: string;
  deliverables: readonly string[];
}

export const PHASES: readonly Phase[] = [
  {
    id: 0,
    title: "Fundação",
    version: "v0.1.0",
    status: "done",
    summary: "Repositório público, documentação viva, CI/CD e este site no ar desde o primeiro commit.",
    deliverables: ["Roadmap e ADRs", "Geometria do campo", "CI + GitHub Pages"],
  },
  {
    id: 1,
    title: "Dados e detecção",
    version: "v0.2.0",
    status: "next",
    summary: "Dataset rotulado, fine-tuning do RF-DETR na GPU local e comparação com um baseline YOLO.",
    deliverables: ["Pipeline de dados", "Modelo ajustado", "Relatório de mAP"],
  },
  {
    id: 2,
    title: "Rastreamento e times",
    version: "v0.3.0",
    status: "planned",
    summary: "Identificadores estáveis com ByteTrack e separação automática de times por aparência.",
    deliverables: ["IDs estáveis", "Classificador de times", "Vídeo anotado"],
  },
  {
    id: 3,
    title: "Calibração do campo",
    version: "v0.4.0",
    status: "planned",
    summary: "Pontos do gramado detectados em cada frame geram a homografia que leva pixels para metros.",
    deliverables: ["Modelo de keypoints", "Homografia suavizada", "Radar 2D"],
  },
  {
    id: 4,
    title: "Leitura tática",
    version: "v0.5.0",
    status: "planned",
    summary: "Formação por janela com confiança, linhas, largura, profundidade, compactação e mapas de calor.",
    deliverables: ["Detector de formação", "Métricas coletivas", "Linha do tempo"],
  },
  {
    id: 5,
    title: "Mesa tática web",
    version: "v1.0.0",
    status: "planned",
    summary: "Vídeo e campo 2D sincronizados, com partidas pré-processadas publicadas aqui. Marco do MVP.",
    deliverables: ["Player sincronizado", "Painel de métricas", "Partidas de demonstração"],
  },
  {
    id: 6,
    title: "Processamento sob demanda",
    version: "v1.1.0",
    status: "planned",
    summary: "API FastAPI com worker e Docker para processar vídeos novos, com demo de upload opcional.",
    deliverables: ["API + worker", "Docker", "Demo de upload"],
  },
  {
    id: 7,
    title: "Apresentação final",
    version: "v1.2.0",
    status: "planned",
    summary: "Apresentação documentando todas as etapas e vídeo explicando o projeto.",
    deliverables: ["Apresentação", "Roteiro", "Vídeo"],
  },
];

export const STATUS_LABEL: Record<PhaseStatus, string> = {
  done: "Concluída",
  active: "Em andamento",
  next: "Próxima",
  planned: "Planejada",
};

/** Frase curta de status exibida no topo do site, derivada do roadmap. */
export function statusHeadline(phases: readonly Phase[] = PHASES): string {
  const active = phases.find((phase) => phase.status === "active");
  if (active) return `Fase ${active.id} · ${active.title} em andamento`;
  const done = phases.filter((phase) => phase.status === "done").at(-1);
  const next = phases.find((phase) => phase.status === "next");
  if (done && next) return `Fase ${done.id} concluída · próxima: ${next.title}`;
  return "Em desenvolvimento";
}

/** Versão da última fase concluída, ou `undefined` antes do primeiro lançamento. */
export function currentVersion(phases: readonly Phase[] = PHASES): string | undefined {
  return phases.filter((phase) => phase.status === "done").at(-1)?.version;
}
