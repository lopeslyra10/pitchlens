# Dados

Vídeos, datasets e pesos de modelos **não são versionados** neste repositório (ver
`.gitignore`): são arquivos grandes e, no caso dos vídeos de partidas, sujeitos a licenças de
terceiros.

## Estrutura local

```text
data/
├── raw/         # vídeos originais (clipes de ~30 s)
├── interim/     # frames extraídos e recortes
└── processed/   # artefatos do pipeline (JSON de análise por partida)
```

## Fontes planejadas

| Fonte | Uso | Licença |
| --- | --- | --- |
| Clipes da competição *DFL – Bundesliga Data Shootout* (Kaggle) | Desenvolvimento e demonstração do pipeline | Sujeita às regras da competição; por isso os vídeos não são redistribuídos aqui |
| Datasets rotulados públicos (jogadores, goleiros, árbitros e bola; pontos do gramado) | Treino e validação dos modelos (Fases 1 e 3) | A confirmar na página de cada dataset e registrar na Fase 1 |

Os scripts de download, a origem exata de cada arquivo e as licenças confirmadas serão
documentados na Fase 1. A decisão sobre a fonte de vídeo está no
[ADR-0001](../docs/adr/0001-fonte-de-video-clipes-bundesliga.md).
