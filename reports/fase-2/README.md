# Relatório da Fase 2: rastreamento e times

Resultados no clipe `u17-nz-can-25` (45 s, 1280×720, 30 fps, câmera na mão, times de branco e
de vermelho), com o detector da Fase 1. Os arquivos desta pasta podem ser recriados com os
comandos indicados.

![Jogadoras rastreadas com número, cor do time e rastro](../../docs/assets/fase-02-rastreamento.gif)

## 1. Rastreamento

`pitchlens track data/raw/u17-nz-can-25.webm --weights PESOS --tracker botsort` (e `bytetrack`)

Sem rótulos de identidade, a estabilidade é medida por indicadores indiretos
(`pitchlens.tracking.stats`): quantos identificadores são criados e quanto tempo cada rastro
dura. Detalhes em [rastreamento-botsort.json](rastreamento-botsort.json) e
[rastreamento-bytetrack.json](rastreamento-bytetrack.json).

| Configuração | Identificadores | Duração mediana | Rastros < 1 s |
| --- | --- | --- | --- |
| `sv.ByteTrack`, detecções a partir de 0,35 (primeira versão) | 329 | 0,5 s | 67% |
| ByteTrack do pacote `trackers`, detecções a partir de 0,1 | 86 | 3,5 s | **23%** |
| **BoT-SORT** do pacote `trackers`, detecções a partir de 0,1 | **78** | **3,8 s** | 28% |

**Leitura:**

- O maior ganho veio de **entregar as detecções fracas ao rastreador**. ByteTrack e BoT-SORT
  usam essas detecções numa segunda associação, para não perder o jogador em frames difíceis.
- O **BoT-SORT** cria menos identificadores e mantém rastros mais longos, porque compensa o
  movimento da câmera. A diferença para o ByteTrack é pequena neste clipe.
- Os identificadores que sobram não são todos erro: em 45 s de câmera panorâmica, jogadoras
  saem e voltam ao quadro, e sem reidentificação por aparência voltam com outro número.

## 2. Separação de times

`python scripts/team_sheet.py data/raw/u17-nz-can-25.webm --weights PESOS`

A folha reúne 111 recortes de jogadores detectados em 12 frames espaçados, agrupados pelo time
previsto **para cada detecção isolada**, sem o voto por identificador que o pipeline usa. A
conferência foi feita visualmente, recorte a recorte, em [times-u17-nz-can-25.jpg](times-u17-nz-can-25.jpg).

| Versão do classificador | Time certo | Trocas de time | Sem time | Ambíguos |
| --- | --- | --- | --- | --- |
| K-means com dois grupos | 98 | **9** | 0 | 4 |
| **Ajuste robusto e rejeição de cores distantes** | 102 | **0** | 5 jogadoras encobertas | 4 |

- Das 9 trocas da primeira versão, **8 nem eram jogadoras**: 4 árbitras de preto e 4 pessoas
  fora do jogo marcadas como "jogador" pelo detector. O classificador era obrigado a escolher
  um dos dois times.
- O **ajuste robusto** descarta as cores mais distantes de cada time antes de recalcular o
  centro. Assim o vermelho aprendido deixou de ser puxado para o escuro pela arbitragem e
  passou de `#94374A` para `#A82F46`.
- A **rejeição** deixa sem time as cores fora do raio dos dois uniformes. Na versão final,
  arbitragem e pessoas de fora passaram a "sem time", que é a resposta correta para elas.
- As 5 jogadoras que ficaram sem time estavam encobertas ou borradas no frame. No vídeo,
  o voto por identificador mantém o time que ela acumulou nos outros frames.

**Limitações:**

- Os parâmetros foram ajustados neste mesmo clipe. A gravação própria (issue #15) vai servir
  de validação independente.
- Um goleiro de uniforme verde é descartado pelo filtro de gramado e aparece sem time. A
  atribuição por posição resolve os goleiros que o detector reconhece como "goleiro".
- A conferência visual foi feita por quem desenvolveu o classificador. A folha é pública para
  que qualquer pessoa possa refazer a contagem.

## Créditos

Vídeo original de [NaBUru38](https://commons.wikimedia.org/wiki/File:2018_FIFA_U-17_Women%27s_World_Cup_-_New_Zealand_vs_Canada_-_25.webm)
no Wikimedia Commons, sob [CC BY-SA 4.0](https://creativecommons.org/licenses/by-sa/4.0/).
As imagens e o vídeo anotados desta fase derivam dele e são distribuídos sob a mesma licença.
