# ADR-0004: Vídeos de licença livre e gravação própria como fonte de vídeo

- **Status:** aceito (substitui o [ADR-0001](0001-fonte-de-video-clipes-bundesliga.md))
- **Data:** 2026-09-16
- **Fase:** 1

## Contexto

O [ADR-0001](0001-fonte-de-video-clipes-bundesliga.md) escolheu os clipes da competição
*DFL – Bundesliga Data Shootout* (Kaggle) e deixou a revisão da licença para depois. Ao ler as
regras da competição, antes de baixar qualquer arquivo, ficou claro que esses vídeos não podem
ser usados neste projeto:

- o uso é restrito à participação na competição e às discussões no fórum do Kaggle;
- é proibido usá-los depois do fim da competição, em qualquer outra finalidade;
- as cópias locais devem ser apagadas ao fim da competição;
- é proibido publicar ou compartilhar os vídeos com quem não aceitou as regras.

Além disso, a página da competição informa que os dados não estão mais disponíveis. As cópias
que circulam em outros sites têm a mesma origem, então as mesmas regras continuam valendo.

## Decisão

1. **Nenhum vídeo da competição é usado**, nem por meio de cópias em outros sites.
2. **Vídeos de licença livre**, escolhidos pelo ângulo alto e pela licença, servem para
   desenvolver e demonstrar o pipeline agora. A origem, o autor e a licença de cada um ficam
   registrados em `data/sources.json`:

   | Arquivo | Origem | Ângulo | Duração | Licença |
   | --- | --- | --- | --- | --- |
   | `pexels-2657261.mp4` | Pexels | Alto e aberto, jogo 11 contra 11 | 13 s | Licença Pexels |
   | `pexels-28870860.mp4` | Pexels | Drone, vista de cima | 60 s | Licença Pexels |
   | `u17-nz-can-25.webm` | Wikimedia Commons | Arquibancada, baixo | 45 s | CC BY-SA 4.0 |

3. **Gravação própria** de um jogo amador, de um ponto elevado e com a câmera parada, será a
   fonte principal da leitura tática (Fase 4), que precisa de vários minutos contínuos de
   jogo.
4. **O treino do detector continua** com o dataset
   [football-players-detection](https://universe.roboflow.com/roboflow-jvuqo/football-players-detection-3zvbc),
   publicado pela Roboflow sob CC BY 4.0.

## Alternativas consideradas

| Alternativa | Por que não |
| --- | --- |
| Cópias dos clipes da competição em outros sites | Mesmo material, sujeito às mesmas regras |
| Transmissões de TV | Direitos das ligas e emissoras |
| Só gravação própria | Bloquearia o desenvolvimento até a gravação acontecer |

## Consequências

- **Mudança de domínio.** O detector aprende com imagens de câmera de transmissão e é usado em
  vídeos com outros ângulos. A queda de precisão deve ser medida e documentada; se for grande,
  anotar alguns frames dos vídeos novos para o ajuste fino passa a ser uma tarefa da fase.
- **Calibração mais simples.** Com câmera fixa ou vista de cima, a homografia da Fase 3 pode ser
  estimada uma vez por trecho em vez de a cada frame. A interface plugável prevista no
  ADR-0001 continua válida.
- **Clipes curtos.** Os vídeos livres bastam para detecção, rastreamento e campo 2D, mas não para
  medir formação com confiança. A leitura tática depende da gravação própria.
- **Share-alike.** Vídeos e imagens derivados do clipe da Wikimedia precisam ser publicados sob
  CC BY-SA 4.0, com atribuição ao autor.
- **Ressalva sobre o dataset.** As imagens do dataset da Roboflow parecem vir de transmissões
  profissionais. O uso segue a licença CC BY 4.0 declarada por quem o publicou, com atribuição,
  e nenhuma dessas imagens é publicada no site.
