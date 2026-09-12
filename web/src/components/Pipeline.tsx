import { PIPELINE } from "../data/pipeline";

export function Pipeline() {
  return (
    <ol className="pipeline">
      {PIPELINE.map((step, index) => (
        <li key={step.title} className="pipeline-step">
          <span className="step-index">{String(index + 1).padStart(2, "0")}</span>
          <span className="step-phase">Fase {step.phase}</span>
          <h3>{step.title}</h3>
          <p>{step.description}</p>
          <span className="step-tech">{step.tech}</span>
        </li>
      ))}
    </ol>
  );
}
