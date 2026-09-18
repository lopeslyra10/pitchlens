# Changelog

Todas as mudanças relevantes do projeto são registradas aqui.

O formato segue o [Keep a Changelog](https://keepachangelog.com/pt-BR/1.1.0/) e o projeto usa
[Versionamento Semântico](https://semver.org/lang/pt-BR/). Cada fase do roadmap fecha com uma
versão.

## [Não lançado]

## [0.2.0] - 2026-09-18

Fase 1: Dados e detecção.

### Adicionado

- Detector RF-DETR Medium ajustado para futebol (bola, goleiro, jogador e árbitro), escolhido
  no ADR-0005 depois da comparação com um baseline YOLO26m.
- Comando `pitchlens detect`, que gera o vídeo anotado de um clipe.
- Leitura e escrita de vídeo em H.264 compatível com navegador.
- Scripts de download de dados com origem e licença registradas em `data/sources.json`.
- Scripts de treino do RF-DETR (com `--resume` e `--grad-accum`) e do YOLO, isolado em
  `scripts/benchmark` por ser AGPL-3.0.
- Avaliador comum e medição do detector fora do ângulo de transmissão, com relatórios em
  `reports/fase-1`.
- ADR-0004 (vídeos de licença livre) e ADR-0005 (escolha do detector).

### Alterado

- ADR-0001 substituído pelo ADR-0004: os clipes da Bundesliga não são usados.
- Dependências de visão computacional movidas para extras opcionais (`cv`, `data`, `bench`).

### Corrigido

- Leitura e escrita de texto em UTF-8 explícito, necessária no Windows com caminhos acentuados.
- Saída de console em UTF-8 nos scripts e na CLI.
- RF-DETR carregado na resolução do treino, e não na padrão de 576 px.

## [0.1.0] - 2026-09-12

Fase 0: Fundação.

### Adicionado

- Repositório público com licença MIT, Conventional Commits e versionamento semântico.
- Documentação de visão, roadmap em oito fases e ADRs 0001 a 0003.
- Núcleo Python `pitchlens.pitch`: dimensões oficiais do campo, 29 pontos de referência para
  a homografia e normalização da direção de ataque, com testes.
- Site em Vite + React + TypeScript com mesa tática simulada e métricas calculadas em tempo
  real.
- CI com ruff, pytest (Python 3.11 e 3.13), Vitest, checagem de tipos e build.
- Deploy contínuo no GitHub Pages.
- Diário de bordo da Fase 0.

[Não lançado]: https://github.com/lopeslyra10/pitchlens/compare/v0.2.0...HEAD
[0.2.0]: https://github.com/lopeslyra10/pitchlens/compare/v0.1.0...v0.2.0
[0.1.0]: https://github.com/lopeslyra10/pitchlens/releases/tag/v0.1.0
