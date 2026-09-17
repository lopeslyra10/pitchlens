# Roadmap

O PitchLens é construído em fases curtas. Cada fase fecha com uma **versão** (tag e release no
GitHub), uma entrada no **[diário de bordo](devlog/)** e imagens do resultado. Esse material é a
base da apresentação final e do vídeo do projeto.

| Fase | Tema | Versão | Status |
| --- | --- | --- | --- |
| 0 | Fundação | v0.1.0 | ✅ Concluída |
| 1 | Dados e detecção | v0.2.0 | ⏭️ Próxima |
| 2 | Rastreamento e times | v0.3.0 | ⚪ Planejada |
| 3 | Calibração do campo | v0.4.0 | ⚪ Planejada |
| 4 | Leitura tática | v0.5.0 | ⚪ Planejada |
| 5 | Mesa tática web (MVP) | v1.0.0 | ⚪ Planejada |
| 6 | Processamento sob demanda | v1.1.0 | ⚪ Planejada |
| 7 | Apresentação final e vídeo | v1.2.0 | ⚪ Planejada |

---

## Fase 0: Fundação (v0.1.0)

**Objetivo:** projeto público, documentado e com deploy automático desde o primeiro commit.

- Convenções de repositório: Conventional Commits, SemVer e CHANGELOG.
- Visão, roadmap e ADRs das decisões iniciais.
- Núcleo Python com a geometria do campo (referencial em metros) e testes.
- Site com mesa tática simulada, publicado no GitHub Pages.
- CI (lint, testes, build) e deploy contínuo com GitHub Actions.

**Pronto quando:** CI verde, site no ar e devlog da fase publicado.

## Fase 1: Dados e detecção (v0.2.0)

**Objetivo:** detectar jogadores, goleiros, árbitros e bola com um modelo ajustado para futebol.

- Scripts de download e organização dos dados, sem versionar vídeos.
- Vídeos de licença livre para os testes, com origem e licença registradas (ADR-0004).
- Fine-tuning do RF-DETR na GPU local (RTX 3060, 12 GB).
- Baseline YOLO no mesmo dataset e comparação de mAP@50, mAP@50-95 e FPS.
- Relatório de avaliação com erros típicos: bola pequena, oclusões, jogadores cortados na borda.
- ADR com a escolha do modelo e a licença dos pesos.

**Pronto quando:** métricas publicadas no devlog e um vídeo de licença livre processado com
caixas desenhadas, com a queda de precisão fora do ângulo de transmissão medida.
**Risco principal:** a bola ocupa poucos pixels; se necessário, inferência em blocos (tiles) ou
um modelo dedicado à bola.

## Fase 2: Rastreamento e times (v0.3.0)

**Objetivo:** cada jogador com um identificador estável e o time correto.

- ByteTrack com tratamento de oclusões e reentrada em cena.
- Separação de times por aparência: embeddings visuais, redução de dimensionalidade e
  clustering; goleiros atribuídos pela proximidade com o próprio time.
- Vídeo anotado com IDs, cores de time e trajetórias.

**Pronto quando:** trocas de ID por minuto e acurácia da separação de times medidas em frames
rotulados manualmente.

## Fase 3: Calibração do campo (v0.4.0)

**Objetivo:** converter pixels da câmera em metros no campo.

- Modelo de pontos do gramado (os pontos de referência já estão em `src/pitchlens/pitch.py`).
- Homografia por frame com RANSAC, suavização temporal e descarte de frames ruins.
- Calibração plugável: por pontos detectados (câmera móvel) ou estática (câmera fixa).
- Radar 2D sincronizado com o vídeo.

**Pronto quando:** erro de reprojeção medido em metros em frames anotados.

## Fase 4: Leitura tática (v0.5.0)

**Objetivo:** transformar posições em conclusões táticas.

- Posições suavizadas em janelas de 5 a 10 s, com cada time normalizado atacando para a direita.
- Formação por atribuição ótima (algoritmo húngaro) contra modelos de formação, com nível de
  confiança (por exemplo, `4-3-3 · 82%`).
- Linhas de defesa, meio e ataque; altura do bloco e distância entre linhas.
- Largura, profundidade, área ocupada, mapas de calor e linha do tempo de mudanças.

**Pronto quando:** formação validada contra rótulos manuais em janelas selecionadas.

## Fase 5: Mesa tática web (v1.0.0, MVP)

**Objetivo:** a experiência completa no navegador.

- Vídeo e campo 2D sincronizados, com linha do tempo de mudanças de formação.
- Painel de métricas por janela e por jogador.
- Partidas de demonstração pré-processadas, a partir de vídeos de licença livre ou gravação própria (ADR-0004).
- Contrato de dados JSON versionado (ADR-0002).

**Pronto quando:** qualquer pessoa consegue abrir o site e explorar uma partida analisada.

## Fase 6: Processamento sob demanda (v1.1.0)

**Objetivo:** processar vídeos novos sem rodar scripts manualmente.

- API FastAPI com worker em fila.
- Docker Compose para rodar tudo localmente com GPU.
- Demo de upload com limite de duração (por exemplo, no Hugging Face Spaces).

## Fase 7: Apresentação final e vídeo (v1.2.0)

**Objetivo:** contar a história do projeto.

- Apresentação construída a partir dos devlogs: problema, arquitetura, cada fase, métricas e
  aprendizados.
- Roteiro e gravação do vídeo explicando o projeto.
- README final com GIFs de cada etapa.

---

## Ideias para depois do MVP

- Intensidade de pressão (alta, média, baixa) e gatilhos de pressão.
- Transições ofensivas e defensivas.
- Corredores mais usados, sobrecargas e superioridade numérica.
- Padrões de saída de bola e comparação entre primeiro e segundo tempo.
- Relatórios automáticos por jogador e por equipe.
- Suporte à transmissão de TV completa, com detecção de cortes e replays.
- Reaproveitamento do núcleo de rastreamento em outros domínios (varejo, indústria, trânsito).
