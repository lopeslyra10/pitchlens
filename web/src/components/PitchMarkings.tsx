import { PITCH } from "../lib/pitch";

const STRIPES = 14;
const CORNER_RADIUS = 1;
const GOAL_DEPTH = 1.6;

/** Gramado e marcações oficiais do campo, em metros (viewBox do SVG = campo real). */
export function PitchMarkings() {
  const { length, width } = PITCH;
  const cy = width / 2;
  const radius = PITCH.centerCircleRadius;
  const penaltyTop = cy - PITCH.penaltyAreaWidth / 2;
  const goalAreaTop = cy - PITCH.goalAreaWidth / 2;
  // A meia-lua é o trecho do círculo de 9,15 m em volta da marca do pênalti fora da grande área.
  const arcDx = PITCH.penaltyAreaDepth - PITCH.penaltySpotDistance;
  const arcDy = Math.sqrt(radius ** 2 - arcDx ** 2);
  const stripeWidth = length / STRIPES;
  const r = CORNER_RADIUS;

  return (
    <g aria-hidden="true">
      <rect className="pitch-grass" x={0} y={0} width={length} height={width} />
      {Array.from({ length: STRIPES }, (_, i) =>
        i % 2 === 1 ? (
          <rect
            key={i}
            className="pitch-stripe"
            x={i * stripeWidth}
            y={0}
            width={stripeWidth}
            height={width}
          />
        ) : null,
      )}
      <g className="pitch-lines">
        <rect x={0} y={0} width={length} height={width} />
        <line x1={length / 2} y1={0} x2={length / 2} y2={width} />
        <circle cx={length / 2} cy={cy} r={radius} />
        <circle className="spot" cx={length / 2} cy={cy} r={0.35} />
        {[
          { side: "left", goalX: 0, direction: 1 },
          { side: "right", goalX: length, direction: -1 },
        ].map(({ side, goalX, direction }) => {
          const left = side === "left";
          const arcX = goalX + direction * PITCH.penaltyAreaDepth;
          return (
            <g key={side}>
              <rect
                x={left ? 0 : length - PITCH.penaltyAreaDepth}
                y={penaltyTop}
                width={PITCH.penaltyAreaDepth}
                height={PITCH.penaltyAreaWidth}
              />
              <rect
                x={left ? 0 : length - PITCH.goalAreaDepth}
                y={goalAreaTop}
                width={PITCH.goalAreaDepth}
                height={PITCH.goalAreaWidth}
              />
              <circle
                className="spot"
                cx={goalX + direction * PITCH.penaltySpotDistance}
                cy={cy}
                r={0.3}
              />
              <path
                d={`M ${arcX} ${cy - arcDy} A ${radius} ${radius} 0 0 ${left ? 1 : 0} ${arcX} ${cy + arcDy}`}
              />
              <rect
                className="goal"
                x={left ? -GOAL_DEPTH : length}
                y={cy - PITCH.goalWidth / 2}
                width={GOAL_DEPTH}
                height={PITCH.goalWidth}
              />
            </g>
          );
        })}
        <path d={`M ${r} 0 A ${r} ${r} 0 0 1 0 ${r}`} />
        <path d={`M ${length - r} 0 A ${r} ${r} 0 0 0 ${length} ${r}`} />
        <path d={`M 0 ${width - r} A ${r} ${r} 0 0 1 ${r} ${width}`} />
        <path d={`M ${length} ${width - r} A ${r} ${r} 0 0 0 ${length - r} ${width}`} />
      </g>
    </g>
  );
}
