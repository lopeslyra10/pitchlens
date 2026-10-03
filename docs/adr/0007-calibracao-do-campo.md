# ADR-0007: Calibração do campo por pontos do gramado, com homografia robusta e medida em metros

- **Status:** aceito
- **Data:** 2026-10-03
- **Fase:** 3

## Contexto

A leitura tática (Fase 4) precisa de posições em metros, não em pixels: distância entre linhas,
largura e compactação só existem no campo. Como o gramado é plano, uma homografia 3x3 leva um
ponto da imagem para o campo — desde que se conheçam pelo menos quatro pontos correspondentes.

Os 32 pontos de referência do gramado já estavam descritos em `src/pitchlens/pitch.py`. Faltava
descobri-los em cada frame e transformá-los em matriz, com três dificuldades práticas: o modelo
erra alguns pontos, a matriz reestimada a cada frame faz o campo "tremer", e em replay, close no
banco ou corte de câmera não há pontos suficientes para calibrar coisa alguma.

## Decisão

1. **Modelo de pontos:** RF-DETR em modo keypoints (preview), ajustado no dataset
   [football-field-detection v18](https://universe.roboflow.com/roboflow-jvuqo/football-field-detection-f07vi)
   (CC BY 4.0, 255 imagens de treino), com os **learning rates padrão do RF-DETR**
   (1e-4 e 1,5e-4) e média móvel dos pesos ligada.
2. **Ajuste da homografia em NumPy** (DLT normalizado mais RANSAC escrito à mão), para rodar na
   CI sem GPU nem OpenCV e dar sempre o mesmo resultado para a mesma entrada.
3. **O RANSAC julga os pontos em metros** (1,5 m), e não em pixels: é a unidade que importa para
   a leitura tática, e ela aperta justamente onde a homografia é mais sensível, nos pontos
   distantes.
4. **Suavização na posição dos pontos projetados**, não na matriz: média de matrizes não tem
   significado geométrico, posição de ponto tem. Um corte de câmera é detectado pelo erro e
   apaga o histórico.
5. **Três guardas antes de aceitar um frame:** erro de reprojeção até 3 m, apoio de pelo menos
   metade dos pontos vistos (e nunca menos de 6) e **campo projetado convexo** — os quatro
   cantos têm de formar um quadrilátero possível, na mesma ordem e do mesmo lado do horizonte.
6. **Frames descartados repetem a última matriz boa por meio segundo** e depois declaram
   "sem campo", em vez de inventar posições.
7. **Máscara do campo pelo pé do jogador:** o meio da base da caixa é o único ponto que toca o
   plano do gramado, e é ele que decide quem está em campo (com 2 m de tolerância). O filtro
   roda antes do rastreador, para que ninguém do banco ganhe identificador.

## Alternativas consideradas

- **RANSAC em pixels.** É o que a literatura clássica faz, porque o ruído do modelo é em pixels.
  Medido nas 28 imagens do split de teste, piorou: 25 imagens calibradas contra 27, e erro
  mediano de 0,53 m contra 0,51 m. Descartado pela medição.
- **Somar os pontos de vários frames** quando a câmera está quase parada, para dar mais material
  ao RANSAC. Nos vídeos da arena salvou 1 frame em 360: o erro do modelo é um viés por ponto, e
  não ruído, então repetir o mesmo ponto em 15 frames repete o mesmo erro. Descartado.
- **Calibração manual por clipe** (marcar quatro pontos à mão). Funciona com câmera fixa e seria
  mais preciso hoje, mas não escala para vídeo com câmera móvel nem se sustenta como projeto.
  Fica como plano B para a gravação própria da Fase 4.
- **OpenCV `findHomography`.** Pronto e testado, mas traria o OpenCV para dentro do núcleo (hoje
  ele só aparece na leitura de vídeo e no desenho) e deixaria a CI sem como testar o ajuste.

## Consequências

- **O erro de reprojeção não prova que a calibração está certa.** Com poucos pontos amontoados,
  a matriz passa por eles com erro baixo e desenha um campo torto no resto da imagem. Por isso a
  checagem geométrica entrou; ela aprova 97% das homografias feitas com anotação e corta 43% dos
  ajustes aceitos nos vídeos da arena.
- **A métrica do treino não serve para decidir nada aqui.** A OKS usa a área do objeto como
  tolerância, e o objeto é o campo inteiro: um modelo com OKS mAP 0,885 não calibrou nenhuma das
  28 imagens de teste. Toda decisão desta fase usa o erro em metros.
- **O domínio do dataset é câmera tática de transmissão.** Nas imagens de teste o modelo calibra
  27 de 28 com 0,51 m; nas gravações da arquibancada ele acerta "quase" (92% dos frames no corte
  da jogada, com o desenho errando um a dois metros em alguns trechos) e falha onde só aparece o
  círculo central. Fechar essa diferença pede anotar imagens do próprio domínio (Fase 4).
- **A escolha do que filmar passa a importar.** Um quadro com grande área e linha de fundo
  calibra bem; um quadro centrado no meio-campo não, porque os pontos ficam quase todos sobre a
  linha do meio e a geometria fica mal condicionada.
