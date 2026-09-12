import { STATUS_LABEL, type Phase } from "../data/roadmap";

interface RoadmapProps {
  phases: readonly Phase[];
}

export function Roadmap({ phases }: RoadmapProps) {
  return (
    <ol className="roadmap">
      {phases.map((phase) => (
        <li key={phase.id} className={`phase phase-${phase.status}`}>
          <div className="phase-meta">
            <span className="phase-id">Fase {phase.id}</span>
            <span className={`status status-${phase.status}`}>{STATUS_LABEL[phase.status]}</span>
            <span className="phase-version">{phase.version}</span>
          </div>
          <h3>{phase.title}</h3>
          <p>{phase.summary}</p>
          <ul className="deliverables">
            {phase.deliverables.map((deliverable) => (
              <li key={deliverable}>{deliverable}</li>
            ))}
          </ul>
        </li>
      ))}
    </ol>
  );
}
