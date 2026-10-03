# Relatório da Fase 3: Calibração do campo

Como medir: a homografia leva cada ponto da imagem para o campo em metros. O erro de
reprojeção é a distância, em metros, entre um ponto de referência levado para o campo e o lugar
onde ele deveria cair. Todos os números abaixo saem de `scripts/evaluate_keypoints.py` no split
de teste do dataset (28 imagens) e da CLI nos vídeos.

## O modelo de pontos do gramado

| | 1º treino | 2º treino |
| --- | --- | --- |
| learning rate (modelo / encoder) | 2e-5 / 2e-5 | **1e-4 / 1,5e-4** (padrão do RF-DETR) |
| média móvel dos pesos | desligada | **ligada** |
| épocas | 60 (teto) | 44 (parada antecipada) |
| duração | ~7 h (duas sessões, a primeira interrompida) | 1 h 09 |
| OKS mAP (métrica do treino) | 0,885 | 1,000 |
| **erro por ponto** | 35,1 px | **12,8 px** |
| **imagens calibradas (28)** | **0** | **27** |

O primeiro treino terminou com uma métrica excelente e um modelo inútil. A OKS usa a área do
objeto como tolerância, e aqui o objeto é o campo inteiro: 50 px de erro ainda pontuam bem. Com
`lr` cinco vezes abaixo do padrão do RF-DETR, o modelo ainda estava aprendendo quando as épocas
acabaram — perdas e métrica caindo na última época.

## Calibração no split de teste

| Pontos usados | Imagens calibradas | Erro mediano | p95 | Máximo |
| --- | --- | --- | --- | --- |
| **modelo** | 27 de 28 (96%) | **0,51 m** | 0,67 m | 0,73 m |
| anotação (teto da geometria) | 28 de 28 (100%) | 0,30 m | 0,48 m | 0,58 m |

A linha de baixo é o controle: com os pontos anotados à mão, o erro não é zero porque a própria
anotação tem ruído. É contra esse teto que o modelo é comparado.

![Campo projetado em quatro imagens do split de teste](../../docs/assets/fase-03-calibracao.jpg)

## Calibração nos vídeos

Cortes de 10 a 12 s da gravação própria (Corinthians x Fluminense, 20/09/2026, Neo Química
Arena), 1080p:

| Vídeo | O que aparece | Frames calibrados | Erro mediano |
| --- | --- | --- | --- |
| `arena-03-jogada` | grande área, linha de fundo e meio campo | 92% | 0,37 m |
| `arena-02-area` | grande área e gol | 83% | 0,33 m |
| `arena-01-circulo` | círculo central e linha do meio | 27% | 0,43 m |

O corte do círculo central é o pior justamente por causa da geometria: os pontos visíveis ficam
quase todos sobre a linha do meio, e quatro pontos quase colineares definem mal uma homografia.
O corte da jogada, com a grande área no quadro, tem pontos espalhados em duas direções.

![Radar 2D com os jogadores em metros, sobre o corte da arena](../../docs/assets/fase-03-radar.jpg)

Rastreamento com calibração ligada no `arena-03-jogada`: 21 identificadores para 14 jogadores
visíveis por frame, 92% dos frames calibrados, erro mediano de 0,37 m.

## O que foi medido e descartado

| Tentativa | Resultado | Decisão |
| --- | --- | --- |
| RANSAC julgando os pontos em pixels | 25 de 28 imagens calibradas (contra 27) e 0,53 m (contra 0,51 m) | descartado |
| Somar pontos de vários frames com câmera parada | salvou 1 frame em 360 | descartado |
| Checagem de campo convexo | mantém 27 de 28 no teste e corta 43% dos ajustes tortos na arena | mantido |

## Limites conhecidos

- **Mudança de domínio.** O dataset é de câmera tática de transmissão, que mostra o campo
  inteiro do alto. As gravações da arquibancada mostram meio campo de um ângulo baixo: o modelo
  acerta "quase", com o desenho errando um a dois metros em alguns trechos. Anotar imagens do
  próprio domínio é tarefa da Fase 4.
- **O erro informado é o dos pontos aceitos.** Ele mede a coerência do ajuste, não a verdade:
  por isso existe a checagem geométrica, e por isso o número do vídeo (0,37 m) não deve ser lido
  como "o radar erra 37 cm".
- **Clipes de drone e de ângulo muito baixo não calibram** (0% no clipe do Pexels e no da U-17),
  o que é coerente: nenhum dos dois se parece com o que o modelo viu no treino.

## Como reproduzir

```bash
python scripts/train_keypoints.py --epochs 60 --batch-size 2 --grad-accum 8 \
    --pretrain runs/keypoints/checkpoint_best_total.pth --output runs/keypoints-v2
python scripts/evaluate_keypoints.py --weights runs/keypoints-v2/last_ema.pth
pitchlens calibrate data/raw/arena-03-jogada.mp4 --weights runs/keypoints-v2/last_ema.pth
pitchlens track data/raw/arena-03-jogada.mp4 \
    --weights runs/rfdetr-medium/checkpoint_best_total.pth \
    --pitch-weights runs/keypoints-v2/last_ema.pth
```

## Créditos e licenças

- Dataset de pontos do gramado: [football-field-detection v18](https://universe.roboflow.com/roboflow-jvuqo/football-field-detection-f07vi),
  Roboflow Universe, CC BY 4.0. As imagens das figuras vêm do split de teste desse dataset.
- Vídeos da arena: gravação do próprio autor, usada no projeto com a sua autorização
  (ver `data/sources.json`).
- Medidas do campo: recomendação da FIFA (105 x 68 m), em `src/pitchlens/pitch.py`.
