import type { PhaseResult, ResultMedia } from "../data/results";

const asset = (path: string) => `${import.meta.env.BASE_URL}${path}`;

function Media({ media }: { media: ResultMedia }) {
  if (media.kind === "video") {
    return (
      <video
        className="result-media"
        src={asset(media.src)}
        poster={media.poster ? asset(media.poster) : undefined}
        aria-label={media.alt}
        autoPlay
        muted
        loop
        playsInline
        preload="metadata"
      />
    );
  }
  return <img className="result-media" src={asset(media.src)} alt={media.alt} loading="lazy" />;
}

export function Results({ results }: { results: readonly PhaseResult[] }) {
  return (
    <div className="results">
      {results.map((result) => (
        <article key={result.phase} className="result">
          <Media media={result.media} />
          <div className="result-body">
            <p className="result-phase">Fase {result.phase}</p>
            <h3>{result.title}</h3>
            <p>{result.summary}</p>
            <dl className="result-metrics">
              {result.metrics.map((metric) => (
                <div key={metric.label}>
                  <dt>{metric.label}</dt>
                  <dd>{metric.value}</dd>
                </div>
              ))}
            </dl>
            <p className="result-credit">
              <a href={result.credit.href}>{result.credit.text}</a> · {result.credit.license}
            </p>
            <a className="result-link" href={result.reportUrl}>
              Ver relatório da fase
            </a>
          </div>
        </article>
      ))}
    </div>
  );
}
