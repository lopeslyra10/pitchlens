# Convenções do projeto

Este repositório é construído em público. As convenções abaixo mantêm o histórico legível e
fazem com que cada fase possa ser apresentada a partir do próprio Git.

## Fluxo de trabalho

- A `main` está sempre publicável: todo push roda a CI e publica o site.
- A partir da Fase 1, cada fase é desenvolvida em uma branch (`feat/fase-1-deteccao`, por
  exemplo) e entra na `main` por pull request com a CI verde.
- Issues e milestones do GitHub acompanham as tarefas de cada fase.

## Proteção da branch `main`

A `main` é protegida por um ruleset no GitHub. Na prática:

- toda mudança entra por **pull request**; não existe push direto;
- **histórico linear**: o merge é por squash ou rebase, nunca por merge commit;
- **force-push e exclusão** da branch são bloqueados;
- os **três checks da CI** precisam passar, e a branch precisa estar atualizada com a `main`
  antes do merge;
- **conversas de revisão** precisam estar resolvidas;
- mudanças **sem autoria atribuída** a uma conta do GitHub exigem aprovação extra, então o
  e-mail dos commits deve ser o mesmo da conta que abre o pull request.

## Commits

Formato `tipo: o que foi feito e por quê`, em português, seguindo
[Conventional Commits](https://www.conventionalcommits.org/pt-br/v1.0.0/). O motivo é a parte
mais importante: quem lê o histórico deve entender a decisão sem abrir o código. Uma linha
costuma bastar; o corpo do commit fica para quando o motivo não couber nela.

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

Quando ajudar a localizar a mudança, o tipo leva um escopo: `core`, `data`, `train`, `track`,
`calib`, `tactics`, `web` ou `api`.

Exemplos:

- `fix(web): linha defensiva calculada só com os zagueiros, porque os laterais avançados distorciam a altura do bloco`
- `feat(calib): suaviza a homografia entre frames para o radar não tremer quando a câmera acompanha a jogada`
- `ci: separa o build do site em outro job para uma falha nos testes Python não bloquear o deploy`

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
- Visão computacional (a partir da Fase 1): o PyTorch com CUDA vem do índice oficial, antes dos
  extras do projeto. O exemplo usa CUDA 13.0; ajuste para o driver da sua GPU.

  ```bash
  pip install torch torchvision --index-url https://download.pytorch.org/whl/cu130
  pip install -e ".[dev,cv,data]" --extra-index-url https://download.pytorch.org/whl/cu130
  pip install -e ".[bench]"   # só para o baseline YOLO (AGPL-3.0)
  ```
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
