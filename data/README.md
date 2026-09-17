# Dados

Vídeos, datasets e pesos de modelos **não são versionados** neste repositório (ver
`.gitignore`): são arquivos grandes e sujeitos às licenças de quem os publicou. O que fica
versionado é o registro das fontes, em `data/sources.json`, gerado pelo script de download.

## Fontes

| Fonte | Uso | Licença |
| --- | --- | --- |
| [football-players-detection](https://universe.roboflow.com/roboflow-jvuqo/football-players-detection-3zvbc), versão 20 (Roboflow Universe) | Treino e avaliação do detector: 372 imagens com bola, goleiro, jogador e árbitro | CC BY 4.0 |
| [Aerial footage of a game of soccer](https://www.pexels.com/video/aerial-footage-of-a-game-of-soccer-2657261/) (Pexels) | Detecção e campo 2D, vista alta e aberta | Licença Pexels |
| [Aerial view of soccer game on green field](https://www.pexels.com/video/aerial-view-of-soccer-game-on-green-field-28870860/), de Benjamin Quezada Arevalo (Pexels) | Campo 2D, drone com vista de cima | Licença Pexels |
| [2018 FIFA U-17 Women's World Cup – New Zealand vs Canada – 25](https://commons.wikimedia.org/wiki/File:2018_FIFA_U-17_Women%27s_World_Cup_-_New_Zealand_vs_Canada_-_25.webm), de NaBUru38 (Wikimedia Commons) | Detecção com ângulo baixo | CC BY-SA 4.0: derivados mantêm a mesma licença |

Os clipes da competição *DFL – Bundesliga Data Shootout* foram descartados porque as regras
proíbem o uso fora da competição. A decisão está no
[ADR-0004](../docs/adr/0004-videos-de-licenca-livre.md).

## Como baixar

1. Copie `.env.example` para `.env` e preencha `ROBOFLOW_API_KEY` (o `.env` não entra no Git).
2. Com o ambiente de visão computacional instalado (ver `CONTRIBUTING.md`), rode:

   ```bash
   python scripts/download_data.py dataset   # dataset em formato YOLO, versão mais recente
   python scripts/download_data.py videos    # vídeos de demonstração de licença livre
   python scripts/download_data.py stats     # imagens por split e instâncias por classe
   ```

O dataset é baixado uma única vez, em formato YOLO, e usado pelos dois modelos. Assim o
RF-DETR e o YOLO são treinados e avaliados exatamente nas mesmas imagens.

## Estrutura local

```text
data/
├── datasets/football-players/   # train/valid/test com images/ e labels/, mais data.yaml
├── raw/                         # vídeos originais
├── interim/                     # frames extraídos e recortes
├── processed/                   # artefatos do pipeline (JSON de análise por partida)
└── sources.json                 # versão do dataset, origem e licença dos vídeos (versionado)
```
