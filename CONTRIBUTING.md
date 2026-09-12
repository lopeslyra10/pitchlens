# Convenções do projeto

Este repositório é construído em público. As convenções abaixo mantêm o histórico legível e
fazem com que cada fase possa ser apresentada a partir do próprio Git.

## Fluxo de trabalho

- A `main` está sempre publicável: todo push roda a CI e publica o site.
- A partir da Fase 1, cada fase é desenvolvida em uma branch (`feat/fase-1-deteccao`, por
  exemplo) e entra na `main` por pull request com a CI verde.
- Issues e milestones do GitHub acompanham as tarefas de cada fase.

## Commits

[Conventional Commits](https://www.conventionalcommits.org/pt-br/v1.0.0/) em português:
`tipo(escopo): descrição no presente`.

| Tipo | Uso |
| --- | --- |
| `feat` | Nova funcionalidade |
| `fix` | Correção de bug |
| `docs` | Documentação, devlog e ADRs |
| `test` | Testes |
| `refactor` | Mudança interna sem alterar comportamento |
| `perf` | Desempenho |
| `ci` | Pipelines de integração e deploy |
| `chore` | Manutenção e configuração |

Escopos usados: `core`, `data`, `train`, `track`, `calib`, `tactics`, `web`, `api`.

Exemplo: `feat(core): adiciona geometria do campo e sistema de coordenadas`.

## Versionamento

[SemVer](https://semver.org/lang/pt-BR/). Cada fase fecha com uma versão (ver
[docs/ROADMAP.md](docs/ROADMAP.md)).

### Checklist de fechamento de fase

1. Entrada da fase em `docs/devlog/`, com imagens em `docs/assets/` e roteiro para o vídeo.
2. ADRs das decisões tomadas durante a fase.
3. `CHANGELOG.md`: mover os itens de "Não lançado" para a nova versão.
4. Atualizar a versão em `pyproject.toml`, `src/pitchlens/__init__.py` e `web/package.json`.
5. Atualizar o status em `docs/ROADMAP.md`, no `README.md` e em `web/src/data/roadmap.ts`.
6. Criar a tag `vX.Y.Z` e a release no GitHub com as imagens da fase.

## Ambiente local

- Python 3.11 ou superior (desenvolvimento em 3.13) e Node 22.12 ou superior.
- Pesos de modelos e caches de pip, npm, PyTorch e Hugging Face podem ocupar vários GB. Se o
  disco do sistema tiver pouco espaço, aponte-os para a pasta `.cache/` do projeto (ignorada
  pelo Git) antes de instalar dependências:

  ```powershell
  $env:PIP_CACHE_DIR = "$PWD\.cache\pip"
  $env:npm_config_cache = "$PWD\.cache\npm"
  $env:TORCH_HOME = "$PWD\.cache\torch"
  $env:HF_HOME = "$PWD\.cache\huggingface"
  $env:TEMP = "$PWD\.cache\tmp"; $env:TMP = $env:TEMP
  ```
