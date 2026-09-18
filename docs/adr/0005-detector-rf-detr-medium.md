# ADR-0005: RF-DETR Medium em 1024 px como detector do pipeline

- **Status:** aceito
- **Data:** 2026-09-18
- **Fase:** 1

## Contexto

O pipeline precisa de um detector de jogadores, goleiros, árbitros e bola ajustado para
futebol. Dois modelos foram treinados na RTX 3060, no mesmo dataset
([football-players-detection](https://universe.roboflow.com/roboflow-jvuqo/football-players-detection-3zvbc)
v20, CC BY 4.0) e na mesma resolução de 1024 px. A bola ocupa cerca de 6 px nas imagens
originais; em resoluções menores, ela praticamente desaparece.

Os dois foram avaliados pelo mesmo código (`scripts/evaluate.py`), no split de teste, com o
mesmo cálculo de mAP e em FP32:

| Modelo | mAP@50 | mAP@50-95 | AP50 bola | AP50 goleiro | AP50 jogador | AP50 árbitro | ms/imagem |
| --- | --- | --- | --- | --- | --- | --- | --- |
| **RF-DETR Medium** | **0,889** | 0,585 | **0,646** | **0,943** | **0,990** | **0,978** | 88,9 |
| YOLO26m | 0,843 | **0,604** | 0,580 | 0,865 | 0,979 | 0,947 | **40,4** |

## Decisão

Usar o **RF-DETR Medium**, ajustado e executado em **1024 px**, como detector padrão.

## Por que

- **Detecta mais, principalmente a bola.** A bola é o objeto mais difícil e o mais importante
  para as fases seguintes (posse, pressão e transições). O RF-DETR vence em todas as classes no
  mAP@50.
- **Licença compatível com o projeto.** O código e o checkpoint Medium são Apache 2.0. O
  Ultralytics YOLO é AGPL-3.0: usar o YOLO na API prevista para a Fase 6 exigiria publicar todo
  o serviço sob AGPL.
- **Latência aceitável neste desenho.** O processamento é offline
  ([ADR-0002](0002-processar-offline-visualizar-online.md)), então 89 ms por frame (cerca de
  11 fps) não bloqueia nada.

## Alternativas consideradas

| Alternativa | Por que não |
| --- | --- |
| YOLO26m | Caixas um pouco mais justas (mAP@50-95) e mais que o dobro da velocidade, mas detecta menos a bola e a licença AGPL-3.0 conflita com a Fase 6 |
| RF-DETR em 576 px (padrão do Medium) | No teste, o AP50 da bola caiu de 0,646 para 0,504 |
| RF-DETR Large | Não testado: o Medium já consome 9,3 GB dos 12 GB da GPU no treino em 1024 px |

## Consequências

- **A bola continua sendo o ponto fraco**, com o modelo encontrando cerca de dois terços delas.
  Inferência em blocos (tiles) ou um detector dedicado entram como tarefa das próximas fases.
- **Fora do ângulo de transmissão, o desempenho cai** (ver o
  [relatório](../../reports/fase-1/README.md)). Com câmera alta aparecem falsos positivos fora
  do gramado, e com drone muito alto os jogadores ficam pequenos demais. O filtro pela área do
  campo chega com a homografia da Fase 3.
- **A resolução precisa acompanhar o checkpoint.** O arquivo de pesos não guarda a resolução;
  o `RFDETRDetector` a lê do `training_config.json` do treino.
- **Otimização pendente.** Os dois modelos foram medidos em FP32. Converter o RF-DETR para FP16
  deve reduzir a latência, e o ganho será medido antes de ser citado.
- **Amostra pequena.** O split de teste tem 25 imagens; diferenças de poucos centésimos estão
  dentro do ruído.
