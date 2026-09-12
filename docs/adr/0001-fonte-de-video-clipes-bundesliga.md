# ADR-0001: Clipes públicos da Bundesliga como fonte de vídeo do MVP

- **Status:** aceito
- **Data:** 2026-09-12
- **Fase:** 0

## Contexto

O MVP precisa de vídeo realista, em que a maior parte do campo apareça, e de dados rotulados
para treinar os modelos de detecção e de pontos do gramado. Três fontes foram avaliadas.

## Alternativas consideradas

| Opção | Vantagens | Desvantagens |
| --- | --- | --- |
| Câmera fixa própria (jogo amador filmado de um ponto elevado) | Direitos 100% próprios; uma única homografia por vídeo | Depende de gravar partidas e rotular dados do zero antes de qualquer avanço |
| Clipes da câmera principal da Bundesliga (competição *DFL – Bundesliga Data Shootout*, Kaggle) | Câmera aberta com qualidade de transmissão; datasets rotulados derivados disponíveis publicamente; resultados comparáveis a projetos de referência | A câmera acompanha a jogada (pan e zoom); vídeos sujeitos às regras da competição |
| Transmissão de TV completa | Cenário mais realista | Cortes, replays, close-ups e zoom constantes; exige detecção de cena antes de qualquer análise |

## Decisão

Usar os **clipes da câmera principal da Bundesliga** no MVP.

## Consequências

- **Homografia por frame.** Como a câmera se move, a calibração não pode ser feita uma única
  vez. A Fase 3 treina um modelo de pontos do gramado e estima a homografia em cada frame, com
  suavização temporal. Os pontos de referência já estão definidos em `src/pitchlens/pitch.py`.
- **Calibração plugável.** O pipeline terá uma interface de calibração com duas implementações:
  por pontos detectados (câmera móvel) e estática (homografia única). Assim, uma câmera fixa
  própria continua possível como evolução, sem reescrever o restante do pipeline.
- **Licença dos vídeos.** Os vídeos não são versionados nem redistribuídos no repositório; o
  download fica documentado em `data/README.md`. Antes de publicar qualquer trecho no site
  (Fase 5), a licença será revista. Se a publicação não for permitida, o site mostra apenas
  dados derivados (posições no campo e métricas) e imagens curtas com atribuição, ou usa
  material de gravação própria.
- **Transmissão completa** fica fora do MVP e entra no roadmap como evolução, com detecção de
  cortes e descarte de frames sem campo visível.
