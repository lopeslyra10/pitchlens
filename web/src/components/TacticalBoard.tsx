import { useEffect, useMemo, useState } from "react";
import type { Vec2 } from "../lib/geometry";
import { PITCH } from "../lib/pitch";
import { boardStateAt } from "../lib/simulation";
import { PitchMarkings } from "./PitchMarkings";

const meters = new Intl.NumberFormat("pt-BR", { maximumFractionDigits: 0 });

function toPoints(points: readonly Vec2[]): string {
  return points.map(([x, y]) => `${x.toFixed(2)},${y.toFixed(2)}`).join(" ");
}

/** Segundos desde a montagem; fica parado em 0 se o usuário preferir menos movimento. */
function useAnimationClock(): number {
  const [seconds, setSeconds] = useState(0);

  useEffect(() => {
    if (window.matchMedia("(prefers-reduced-motion: reduce)").matches) return;
    let frame = 0;
    const origin = performance.now();
    const tick = (now: number) => {
      setSeconds((now - origin) / 1000);
      frame = requestAnimationFrame(tick);
    };
    frame = requestAnimationFrame(tick);
    return () => cancelAnimationFrame(frame);
  }, []);

  return seconds;
}

export function TacticalBoard() {
  const seconds = useAnimationClock();
  const state = useMemo(() => boardStateAt(seconds), [seconds]);
  const { formation, shape } = state;

  return (
    <figure className="board">
      <div className="board-header">
        <span className="board-title">Mesa tática</span>
        <span className="tag">Simulação</span>
      </div>
      <svg
        viewBox={`-3 -3 ${PITCH.length + 6} ${PITCH.width + 6}`}
        role="img"
        aria-label={`Mesa tática simulada: time da casa em ${formation.name}, ${formation.context.toLowerCase()}.`}
      >
        <PitchMarkings />
        <polygon className="hull" points={toPoints(state.hull)} />
        <line
          className="defensive-line"
          x1={state.defensiveLine}
          y1={0}
          x2={state.defensiveLine}
          y2={PITCH.width}
        />
        <g style={{ opacity: state.lineOpacity }}>
          {state.lines.map((line, i) => (
            <polyline key={i} className="unit-line" points={toPoints(line)} />
          ))}
        </g>
        {state.away.map(([x, y], i) => (
          <circle key={i} className="player away" cx={x} cy={y} r={1.5} />
        ))}
        {state.home.map(({ position: [x, y], number, goalkeeper }) => (
          <g key={number} transform={`translate(${x.toFixed(2)} ${y.toFixed(2)})`}>
            <circle className={goalkeeper ? "player home goalkeeper" : "player home"} r={1.9} />
            <text className="player-number">{number}</text>
          </g>
        ))}
        <circle className="ball" cx={state.ball[0]} cy={state.ball[1]} r={0.75} />
      </svg>
      <figcaption>
        <dl className="metrics">
          <div className="metric-formation">
            <dt>Formação</dt>
            <dd>
              {formation.name}
              <span className="metric-context">{formation.context}</span>
            </dd>
          </div>
          <div>
            <dt>Largura</dt>
            <dd>{meters.format(shape.width)} m</dd>
          </div>
          <div>
            <dt>Profundidade</dt>
            <dd>{meters.format(shape.depth)} m</dd>
          </div>
          <div>
            <dt>Linha defensiva</dt>
            <dd>{meters.format(state.defensiveLine)} m</dd>
          </div>
          <div>
            <dt>Área ocupada</dt>
            <dd>{meters.format(shape.area)} m²</dd>
          </div>
        </dl>
        <p className="board-note">
          Posições simuladas; as métricas são calculadas em tempo real no navegador. Na Fase 5,
          esta mesa passa a exibir partidas reais processadas pelo pipeline.
        </p>
      </figcaption>
    </figure>
  );
}
