# Changelog

Todas as mudanças relevantes do projeto são registradas aqui.

O formato segue o [Keep a Changelog](https://keepachangelog.com/pt-BR/1.1.0/) e o projeto usa
[Versionamento Semântico](https://semver.org/lang/pt-BR/). Cada fase do roadmap fecha com uma
versão.

## [Não lançado]

## [0.4.0] - 2026-10-03

Fase 3: Calibração do campo.

### Adicionado

- Modelo de pontos do gramado (RF-DETR keypoints) ajustado nos 32 pontos do dataset
  `football-field-detection`, com `scripts/train_keypoints.py`.
- Homografia por frame em NumPy (DLT normalizado e RANSAC), com suavização pela posição dos
  pontos projetados, detecção de corte de câmera e descarte de frames ruins.
- Checagem geométrica do ajuste: o campo projetado tem de ser um quadrilátero convexo.
- Comando `pitchlens calibrate`, que desenha o campo sobre o vídeo e grava os indicadores.
- Radar 2D e linhas do campo no `pitchlens track`, via `--pitch-weights`.
- Máscara do campo pelo pé do jogador, aplicada antes do rastreador.
- `scripts/evaluate_keypoints.py`: erro dos pontos em pixels e erro de reprojeção em metros,
  com a anotação como teto de comparação; relatório em `reports/fase-3`.
- Três cortes da gravação própria na Neo Química Arena, registrados em `data/sources.json`.
- `scripts/acompanhar-treino.ps1`, para acompanhar treinos que rodam soltos da sessão.
- ADR-0007 (calibração do campo).

### Corrigido

- Treino dos pontos do gramado com os learning rates e a média móvel padrão do RF-DETR: o
  ajuste anterior (2e-5) deixava o modelo subtreinado e sem calibrar nenhuma imagem de teste.

## [0.3.0] - 2026-09-18

Fase 2: Rastreamento e times.

### Adicionado

- Comando `pitchlens track`, que gera o vídeo com número, time e rastro de cada jogador.
- Rastreamento com o BoT-SORT do pacote `trackers`, com compensação do movimento da câmera
  (`--tracker bytetrack` disponível para comparação).
- Separação de times pela cor do tronco, sem rótulos, com ajuste robusto, rejeição de cores
  distantes e voto por identificador; goleiros pelo time mais próximo.
- Indicadores de estabilidade do rastreamento e folha de conferência dos times
  (`scripts/team_sheet.py`), com relatório em `reports/fase-2`.
- Seção "Resultados" no site, com imagem e vídeo reais de cada fase e créditos das licenças.
- ADR-0006 (rastreador e método de times).

### Corrigido

- Clipe do site versionado por exceção no `.gitignore`, que excluía todo `.mp4`.

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

[Não lançado]: https://github.com/lopeslyra10/pitchlens/compare/v0.4.0...HEAD
[0.4.0]: https://github.com/lopeslyra10/pitchlens/compare/v0.3.0...v0.4.0
[0.3.0]: https://github.com/lopeslyra10/pitchlens/compare/v0.2.0...v0.3.0
[0.2.0]: https://github.com/lopeslyra10/pitchlens/compare/v0.1.0...v0.2.0
[0.1.0]: https://github.com/lopeslyra10/pitchlens/releases/tag/v0.1.0
