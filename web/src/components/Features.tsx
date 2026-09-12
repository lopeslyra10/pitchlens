const ICONS = {
  shape: (
    <svg viewBox="0 0 24 24" aria-hidden="true">
      <path d="M5 18 12 6l7 12Z" />
      <circle cx="5" cy="18" r="2.2" />
      <circle cx="12" cy="6" r="2.2" />
      <circle cx="19" cy="18" r="2.2" />
    </svg>
  ),
  chip: (
    <svg viewBox="0 0 24 24" aria-hidden="true">
      <rect x="6" y="6" width="12" height="12" rx="2" />
      <path d="M9 2v4M15 2v4M9 18v4M15 18v4M2 9h4M2 15h4M18 9h4M18 15h4" />
    </svg>
  ),
  globe: (
    <svg viewBox="0 0 24 24" aria-hidden="true">
      <circle cx="12" cy="12" r="9" />
      <path d="M3 12h18M12 3a14 14 0 0 1 0 18M12 3a14 14 0 0 0 0 18" />
    </svg>
  ),
};

const FEATURES = [
  {
    icon: ICONS.shape,
    title: "Leitura tática, não só radar",
    text: "Formação detectada em janelas de tempo com nível de confiança, altura da linha defensiva, distância entre setores e compactação.",
  },
  {
    icon: ICONS.chip,
    title: "Modelos treinados no projeto",
    text: "Detector e pontos do gramado ajustados em GPU local, com métricas publicadas e comparação entre arquiteturas.",
  },
  {
    icon: ICONS.globe,
    title: "Sempre no ar, custo zero",
    text: "O processamento pesado roda offline e o site consome os resultados como arquivos estáticos: sem servidor e sem espera.",
  },
];

export function Features() {
  return (
    <div className="features">
      {FEATURES.map((feature) => (
        <article key={feature.title} className="feature">
          <span className="feature-icon">{feature.icon}</span>
          <h3>{feature.title}</h3>
          <p>{feature.text}</p>
        </article>
      ))}
    </div>
  );
}
