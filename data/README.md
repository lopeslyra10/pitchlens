# Dados

Vídeos, datasets e pesos de modelos **não são versionados** neste repositório (ver
`.gitignore`): são arquivos grandes e, no caso dos vídeos de partidas, sujeitos a licenças de
terceiros. O que fica versionado é o registro das fontes, em `data/sources.json`, gerado pelo
script de download.

## Fontes

| Fonte | Uso | Licença |
| --- | --- | --- |
| [football-players-detection](https://universe.roboflow.com/roboflow-jvuqo/football-players-detection-3zvbc) (Roboflow Universe) | Treino e avaliação do detector, com imagens da câmera principal e as classes bola, goleiro, jogador e árbitro | CC BY 4.0 |
| Clipes de 30 s da competição [DFL – Bundesliga Data Shootout](https://www.kaggle.com/competitions/dfl-bundesliga-data-shootout) (Kaggle) | Inferência em vídeo e demonstração | Regras da competição (cláusula de uso a confirmar); os vídeos não são redistribuídos aqui |

## Como baixar

1. Configure as credenciais. Nenhuma delas entra no Git:
   - **Roboflow:** copie `.env.example` para `.env` e preencha `ROBOFLOW_API_KEY`.
   - **Kaggle:** aceite as regras da competição no site e autentique com `kaggle auth login`
     (ou preencha `KAGGLE_API_TOKEN` no `.env`).
2. Com o ambiente de visão computacional instalado (ver `CONTRIBUTING.md`), rode:

   ```bash
   python scripts/download_data.py dataset   # dataset em formato YOLO, versão mais recente
   python scripts/download_data.py clips     # cinco clipes de 30 s
   python scripts/download_data.py stats     # imagens por split e instâncias por classe
   ```

O dataset é baixado uma única vez, em formato YOLO, e usado pelos dois modelos. Assim o
RF-DETR e o YOLO são treinados e avaliados exatamente nas mesmas imagens.

## Estrutura local

```text
data/
├── datasets/football-players/   # train/valid/test com images/ e labels/, mais data.yaml
├── raw/                         # clipes de vídeo originais
├── interim/                     # frames extraídos e recortes
├── processed/                   # artefatos do pipeline (JSON de análise por partida)
└── sources.json                 # versão do dataset e clipes usados (versionado)
```

A decisão sobre a fonte de vídeo está no
[ADR-0001](../docs/adr/0001-fonte-de-video-clipes-bundesliga.md).
