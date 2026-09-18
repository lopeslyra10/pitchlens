# Fase 1: Dados e detecção

- **Versão:** v0.2.0
- **Período:** 2026-09-12 a 2026-09-18
- **Status:** concluída
- **Pull request:** [#8](https://github.com/lopeslyra10/pitchlens/pull/8)

![Detector em um jogo filmado de uma câmera alta](../assets/fase-01-estadio.jpg)

## Objetivo

Detectar jogadores, goleiros, árbitros e bola com um modelo ajustado para futebol, comparar
com um baseline e medir o resultado de forma justa.

## O que foi feito

- **Ambiente de treino:** PyTorch com CUDA na RTX 3060, com dependências pesadas em extras
  opcionais para a CI seguir sem GPU.
- **Dados:** dataset rotulado da Roboflow (CC BY 4.0, 372 imagens) baixado com a versão
  registrada, e três vídeos de licença livre para testes.
- **Treino:** RF-DETR Medium e YOLO26m, os dois em 1024 px por causa da bola.
- **Avaliação:** um avaliador comum, com o mesmo split, o mesmo limiar e o mesmo cálculo de mAP
  para os dois modelos, mais uma medição de comportamento fora do ângulo de transmissão.
- **Ferramentas:** o comando `pitchlens detect`, que gera o vídeo anotado, e escrita de vídeo em
  H.264 compatível com navegador.
- **Qualidade:** 58 testes; a CI roda os leves e os que dependem de GPU ficam de fora.

## Decisões

- [ADR-0004](../adr/0004-videos-de-licenca-livre.md): vídeos de licença livre e gravação
  própria substituem os clipes da Bundesliga ([ADR-0001](../adr/0001-fonte-de-video-clipes-bundesliga.md)).
- [ADR-0005](../adr/0005-detector-rf-detr-medium.md): RF-DETR Medium em 1024 px como detector.

## Problemas e soluções

| Problema | Causa | Solução |
| --- | --- | --- |
| Os clipes da Bundesliga não podiam ser usados | As regras da competição proíbem o uso fora dela e exigem apagar as cópias | Nenhum clipe foi baixado; vídeos de licença livre e gravação própria (ADR-0004) |
| O treino de teste quebrava ao ler o `data.yaml` | No Windows, o Python grava texto em cp1252 e o caminho do projeto tem "ç" | UTF-8 explícito em toda leitura e escrita, com um teste que analisa o código e barra novas chamadas sem encoding |
| O treino quebrava ao imprimir a tabela de métricas | Com a saída redirecionada para arquivo, o console usa cp1252 | Saída forçada para UTF-8 no início de cada script |
| O treino parou na época 22 | O processo estava preso à sessão do terminal e morreu junto com ela | Processo independente e retomada do checkpoint com `--resume` |
| O treino parou de novo na época 26, e o Windows fechou o Python por travamento | O lote automático escolheu 21 imagens de 1024 px e esgotou os 12 GB da GPU | Lote de 4 com acúmulo de gradiente (`--grad-accum 5`). Cada época caiu de cerca de 8 minutos para pouco mais de 1 |
| O RF-DETR foi pior que o YOLO na primeira comparação | O checkpoint não guarda a resolução e voltava para 576 px, derrubando a bola de 0,646 para 0,504 | O detector lê a resolução do `training_config.json` do treino |
| O YOLO era avaliado em 640 px | Padrão do avaliador diferente da resolução de treino | Resolução configurável, padrão de 1024 px |

Os dois últimos problemas foram os mais importantes: sem conferir de onde vinha a diferença
entre validação e teste, a comparação teria escolhido o modelo errado.

## Resultados

**Comparação no split de teste** (25 imagens, mesmo avaliador, 1024 px, FP32):

| Modelo | mAP@50 | mAP@50-95 | AP50 bola | AP50 goleiro | AP50 jogador | AP50 árbitro | ms/imagem |
| --- | --- | --- | --- | --- | --- | --- | --- |
| **RF-DETR Medium** | **0,889** | 0,585 | **0,646** | **0,943** | **0,990** | **0,978** | 88,9 |
| YOLO26m | 0,843 | **0,604** | 0,580 | 0,865 | 0,979 | 0,947 | **40,4** |

**Fora do ângulo de transmissão** (indicadores por frame, sem rótulos):

| Fonte | Ângulo | Jogadores/frame | Confiança (jogador) | Frames com bola |
| --- | --- | --- | --- | --- |
| Teste do dataset | Transmissão | 20,0 | 0,87 | 80% |
| Wikimedia (U-17) | Arquibancada baixa | 10,4 | 0,83 | 81% |
| Pexels | Estádio, câmera alta | 33,9 | 0,71 | 38% |
| Pexels | Drone muito alto | 7,6 | 0,57 | 6% |

- Com **arquibancada baixa**, o detector se comporta quase como no teste.
- Com **câmera alta**, os jogadores em campo são encontrados, mas pessoas fora do gramado também.
  A máscara do campo da Fase 3 resolve isso.
- Com **drone muito alto**, os jogadores ficam pequenos demais para detectar.

| Arquibancada baixa | Drone muito alto |
| --- | --- |
| ![](../assets/fase-01-arquibancada.jpg) | ![](../assets/fase-01-drone.jpg) |

Relatório completo e créditos das imagens: [reports/fase-1](../../reports/fase-1/README.md).

## Aprendizados

- **Métrica média esconde o problema.** Jogadores passam de 0,97 de AP50; a bola fica em 0,65.
- **Comparar modelos exige o mesmo avaliador e a mesma resolução.** As métricas impressas por
  cada framework não são comparáveis entre si.
- **Licença vem antes do código.** Ler as regras antes do download evitou construir o projeto
  sobre dados que não podiam ser publicados.
- **Treino longo precisa sobreviver a falhas:** checkpoints, retomada e processo independente.

## Roteiro para o vídeo

Cerca de dois minutos:

1. **Gancho (0:00 a 0:15).** Mostrar o vídeo do estádio com as detecções: "o modelo acha os
   jogadores, mas também acha a torcida".
2. **Dados e licença (0:15 a 0:40).** Explicar por que os clipes da Bundesliga ficaram de fora
   e mostrar o ADR-0004.
3. **Dois modelos, um avaliador (0:40 a 1:10).** Mostrar a tabela e contar o bug da resolução:
   "na primeira comparação, o modelo certo parecia o pior".
4. **O que o modelo ainda não resolve (1:10 a 1:40).** A bola com AP50 de 0,65, o drone alto e
   as pessoas fora do campo, cada um ligado à fase que vai tratá-lo.
5. **Próximo passo (1:40 a 2:00).** "Na Fase 2, cada jogador ganha um identificador e um time."

## Próximos passos

Fase 2: rastreamento e times ([milestone](https://github.com/lopeslyra10/pitchlens/milestone/2)).

- ByteTrack sobre as detecções do RF-DETR.
- Separação de times por aparência do uniforme.
- Gravação própria de um jogo com câmera parada, do alto da arquibancada.
- Pendências da Fase 1: detecção da bola (tiles ou modelo dedicado) e medição do RF-DETR em FP16.
