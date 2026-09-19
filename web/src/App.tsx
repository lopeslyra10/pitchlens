import { Features } from "./components/Features";
import { Logo } from "./components/Logo";
import { Pipeline } from "./components/Pipeline";
import { Results } from "./components/Results";
import { Roadmap } from "./components/Roadmap";
import { TacticalBoard } from "./components/TacticalBoard";
import { ADR_URL, AUTHOR, DEVLOG_URL, REPO_URL, ROADMAP_URL } from "./data/project";
import { RESULTS } from "./data/results";
import { PHASES, currentVersion, statusHeadline } from "./data/roadmap";

interface SectionHeadingProps {
  kicker: string;
  title: string;
  text: string;
}

function SectionHeading({ kicker, title, text }: SectionHeadingProps) {
  return (
    <div className="section-heading">
      <p className="section-kicker">{kicker}</p>
      <h2>{title}</h2>
      <p>{text}</p>
    </div>
  );
}

export default function App() {
  const version = currentVersion();

  return (
    <>
      <header className="topbar">
        <div className="container topbar-inner">
          <a className="brand" href="#inicio" aria-label="PitchLens, início">
            <Logo />
            <span>PitchLens</span>
          </a>
          <nav className="nav" aria-label="Seções">
            <a href="#como-funciona">Como funciona</a>
            <a href="#resultados">Resultados</a>
            <a href="#diferenciais">Diferenciais</a>
            <a href="#roadmap">Roadmap</a>
            <a className="nav-cta" href={REPO_URL}>
              GitHub
            </a>
          </nav>
        </div>
      </header>

      <main id="inicio">
        <section className="hero container">
          <div className="hero-copy">
            <p className="eyebrow">
              <span className="pulse" aria-hidden="true" />
              {statusHeadline()}
            </p>
            <h1>
              Do vídeo à <span className="accent">leitura tática</span>.
            </h1>
            <p className="lede">
              O PitchLens usa visão computacional para detectar jogadores, reconstruir o campo em
              2D e identificar formação, linhas e compactação ao longo da partida.
            </p>
            <div className="cta-row">
              <a className="btn btn-primary" href={REPO_URL}>
                Ver código no GitHub
              </a>
              <a className="btn btn-ghost" href={DEVLOG_URL}>
                Diário de bordo
              </a>
            </div>
            <ul className="hero-facts">
              <li>
                <strong>7 etapas</strong>do vídeo ao campo 2D
              </li>
              <li>
                <strong>105 × 68 m</strong>referencial em metros
              </li>
              <li>
                <strong>8 fases</strong>documentadas em público
              </li>
            </ul>
          </div>
          <TacticalBoard />
        </section>

        <section id="como-funciona" className="section">
          <div className="container">
            <SectionHeading
              kicker="Como funciona"
              title="Um pipeline, sete etapas"
              text="Cada etapa tem entrada e saída bem definidas e é construída em uma fase do roadmap."
            />
            <Pipeline />
          </div>
        </section>

        <section id="resultados" className="section">
          <div className="container">
            <SectionHeading
              kicker="Resultados"
              title="O que já funciona, em vídeos reais"
              text="Cada fase publica aqui o resultado do pipeline em vídeos de licença livre, com as métricas medidas no projeto."
            />
            <Results results={RESULTS} />
          </div>
        </section>

        <section id="diferenciais" className="section">
          <div className="container">
            <SectionHeading
              kicker="Diferenciais"
              title="Mais do que pontos num campo"
              text="O radar 2D é o ponto de partida. O objetivo é responder as perguntas que um analista faria."
            />
            <Features />
          </div>
        </section>

        <section id="roadmap" className="section">
          <div className="container">
            <SectionHeading
              kicker="Roadmap"
              title="Construído em público, fase a fase"
              text="Cada fase fecha com uma versão, uma release no GitHub e uma entrada no diário de bordo."
            />
            <Roadmap phases={PHASES} />
            <p className="section-links">
              <a href={ROADMAP_URL}>Roadmap detalhado</a>
              <a href={ADR_URL}>Decisões de arquitetura</a>
              <a href={DEVLOG_URL}>Diário de bordo</a>
            </p>
          </div>
        </section>
      </main>

      <footer className="footer">
        <div className="container footer-inner">
          <span>PitchLens · {version ?? "pré-lançamento"} · Licença MIT</span>
          <span>
            Feito por <a href={AUTHOR.url}>{AUTHOR.name}</a>
          </span>
        </div>
      </footer>
    </>
  );
}
