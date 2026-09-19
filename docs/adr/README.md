# Registros de decisão de arquitetura (ADRs)

Cada decisão relevante do projeto é registrada com contexto, alternativas e consequências, no
formato proposto por
[Michael Nygard](https://cognitect.com/blog/2011/11/15/documenting-architecture-decisions).
Um ADR aceito não é reescrito: se a decisão mudar, um novo ADR substitui o anterior.

| ADR | Decisão | Status |
| --- | --- | --- |
| [0001](0001-fonte-de-video-clipes-bundesliga.md) | Clipes públicos da Bundesliga como fonte de vídeo do MVP | Substituído pelo 0004 |
| [0002](0002-processar-offline-visualizar-online.md) | Processar offline na GPU local e publicar um site estático | Aceito |
| [0003](0003-stack-e-organizacao-do-repositorio.md) | Stack e organização do repositório | Aceito |
| [0004](0004-videos-de-licenca-livre.md) | Vídeos de licença livre e gravação própria como fonte de vídeo | Aceito |
| [0005](0005-detector-rf-detr-medium.md) | RF-DETR Medium em 1024 px como detector do pipeline | Aceito |
| [0006](0006-rastreamento-botsort-e-times-por-cor.md) | BoT-SORT para rastrear e cor do uniforme para separar os times | Aceito |

## Modelo

```markdown
# ADR-NNNN: Título da decisão

- **Status:** proposto | aceito | substituído por ADR-XXXX
- **Data:** AAAA-MM-DD
- **Fase:** N

## Contexto
Qual problema ou restrição motivou a decisão.

## Decisão
O que foi decidido.

## Alternativas consideradas
O que mais foi avaliado e por que ficou de fora.

## Consequências
O que fica mais fácil, o que fica mais difícil e o que precisa ser acompanhado.
```
