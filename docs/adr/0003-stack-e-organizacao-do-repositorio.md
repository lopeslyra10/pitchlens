# ADR-0003: Stack e organização do repositório

- **Status:** aceito
- **Data:** 2026-09-12
- **Fase:** 0

## Contexto

O projeto tem duas partes que evoluem juntas: um núcleo de visão computacional em Python e uma
interface web interativa. Quem visita o repositório precisa conseguir verificar a qualidade das
duas.

## Decisão

**Monorepo** com duas partes:

| Pasta | Conteúdo | Ferramentas |
| --- | --- | --- |
| `src/pitchlens/` | Núcleo Python: geometria do campo e, nas próximas fases, detecção, rastreamento, calibração e leitura tática | Python 3.11+, NumPy; PyTorch, RF-DETR, OpenCV e supervision entram como extras opcionais na Fase 1 |
| `web/` | Site e mesa tática | Vite, React, TypeScript, Vitest |

- **Layout `src/`** no Python, para que os testes rodem contra o pacote instalado.
- **Vite em vez de Next.js.** O site é uma SPA estática centrada em SVG e Canvas, sem SSR nem
  rotas de API. O Vite gera um build estático simples, ideal para o GitHub Pages.
- **Qualidade.** `ruff` (lint e formatação) e `pytest` no Python; checagem de tipos, `vitest` e
  build no web. A CI roda tudo em cada push e pull request, testando o núcleo em Python 3.11 e
  3.13.
- **CI leve.** Dependências pesadas de deep learning ficam em extras opcionais, fora da CI;
  testes que exigem GPU ou pesos de modelo serão marcados e executados localmente.
- **Versionamento.** Conventional Commits em português, SemVer, CHANGELOG no formato Keep a
  Changelog e uma tag com release por fase (ver `CONTRIBUTING.md`).
- **Licença.** MIT para o código do projeto.

## Alternativas consideradas

| Alternativa | Por que não |
| --- | --- |
| Repositórios separados para pipeline e site | Divide a história do projeto e duplica CI e documentação |
| Next.js | Recursos de servidor sem uso aqui; exportação estática com mais configuração |
| Streamlit | Rápido para protótipos, mas limita a mesa tática interativa sincronizada com vídeo |

## Consequências

- Um único repositório conta a história completa: código, decisões, deploy e releases.
- As dimensões do campo existem em dois lugares (`src/pitchlens/pitch.py` e
  `web/src/lib/pitch.ts`). Na Fase 5 o site passa a ler as dimensões do JSON exportado pelo
  pipeline, eliminando a duplicação.
- **Licenças de modelos.** O código do RF-DETR é Apache-2.0 (a licença de cada checkpoint será
  conferida); o Ultralytics YOLO é AGPL-3.0. Se o YOLO for usado como baseline na Fase 1, ficará
  isolado em scripts de benchmark. A escolha final será registrada em um ADR na Fase 1.
