# AGENTS.md — CLI CivilEng

> Instruções para agentes de IA (Hermes, Claude Code, etc.) que trabalham neste repositório.
> Este arquivo define as práticas obrigatórias, convenções e o workflow de desenvolvimento.

---

## Pre-push Checklist (OBRIGATÓRIO)

**Nenhum código sobe para o GitHub sem passar por estes 4 gates.**  
A ordem importa — cada gate desbloqueia o próximo:

### Gate 0: Instalador Audit (ANTES dos demais gates)

**Toda mudança no código precisa de uma verificação de impacto nos instaladores.**

Antes de abrir os outros gates, pergunte-se: "O que eu mudei pode quebrar o `install.sh` ou `install.ps1`?"

| Se você mudou... | Verifique se precisa atualizar... |
|---|---|
| `pyproject.toml` (dependências) | `install.sh` / `install.ps1` — `pip install -e .` já cobre, **mas** se adicionou dependência com build nativo (ex: `pymupdf`) verifique se as libs de sistema estão documentadas |
| Versão mínima do Python | `install.sh:28` e `install.ps1:32` — ambos têm `if major < 3.11` |
| `config.yaml.example` (novos campos) | `install.sh:95` e `install.ps1:90` — o arquivo é copiado como template, então novos campos já aparecem. Mas se mudou a **estrutura** do config, o wrapper pode precisar ser atualizado |
| Estrutura de diretórios (novos `data/`, `projects/`, etc.) | `install.sh` / `install.ps1` — verifique se diretórios git-ignorados precisam ser criados pelo instalador |
| Entry point da CLI (`main.py`, `pyproject.toml [project.scripts]`) | Wrapper em `install.sh:70` e `install.ps1:75` — ambos chamam `python -m cli_civileng.main`. Se o entry point mudar, os wrappers quebram |
| Variáveis de ambiente usadas pela CLI | Wrapper e instalador — documentar no `--help` e verificar se o wrapper as propaga |
| `setup.sh` / `setup.bat` | `install.sh` / `install.ps1` — são versões "one-liner" dos setups. Mudanças em um devem ser refletidas no outro |
| Novo arquivo no repo que o instalador baixa | `.gitignore` — se o arquivo não está no repo, `install.sh` não pode depender dele. Se está no repo e é essencial, verifique se o `--depth 1` do clone pega ele |

**Regra prática:** se você criar/renomear/remover qualquer arquivo na raiz do projeto ou em `cli_civileng/`, passe 30 segundos olhando `install.sh` e `install.ps1` para ver se algo quebrou.

### Gate 1: Code Review (claudecode-code-reviewer)

```bash
python3 ~/.hermes/skills/claude-skills/engineering-team/code-reviewer/scripts/code_quality_checker.py cli_civileng/ --language python --json
```

**Critério de aprovação:**
- Nenhum arquivo com nota **< 80 (B)** deve ser commitado sem justificativa documentada
- Issues `critical` e `high` devem ser resolvidas antes do push
- Issues `medium` precisam de justificativa no commit message se não forem resolvidas
- Issues `low` podem ser registradas como backlog

**A skill carrega automaticamente:**
- `rules/universal.md` — segurança, async, recursos, exceções, performance
- `languages/python.md` — idiomas Python, type hints, exceções, resource management

### Gate 2: Security Review (claudecode-senior-security)

```bash
python3 ~/.hermes/skills/claude-skills/engineering-team/senior-security/scripts/secret_scanner.py . --format json --severity high
```

**Critério de aprovação:**
- **Zero** findings `critical` ou `high` — qualquer secret/API key hardcoded bloqueia o push
- Rotacionar secrets expostos **antes** de commitar (não basta remover do código)
- A skill `claudecode-senior-security` também faz STRIDE threat modeling para novos endpoints/fluxos

### Gate 3: Test Suite (80/80 passing)

```bash
source venv/bin/activate
python3 -m pytest tests/ -v --tb=short
```

**Critério de aprovação:**
- **100% dos testes passando** — zero failures, zero errors
- Testes quebrados por mudanças devem ser corrigidos no mesmo commit
- O comando acima deve rodar limpo do zero (sem estado de execuções anteriores)

---

## Testes: Política de Atualização

### Quando novos testes são OBRIGATÓRIOS

| Situação | Ação |
|----------|------|
| Novo módulo/arquivo `.py` | Criar `tests/test_<modulo>.py` correspondente |
| Nova função pública | Adicionar casos: happy path + edge cases + error handling |
| Bug fix | Adicionar teste de regressão que reproduz o bug |
| Refactor que muda assinatura | Atualizar todos os testes que chamam a função |
| Nova feature | Testes escritos **antes** da implementação (TDD) |

### Cobertura por camada

| Camada | Alvo | Tipo de teste |
|--------|------|---------------|
| `checker/` | 100% | Unitário (funções puras) |
| `extractors/` | 90%+ | Unitário + Integração |
| `llm/` | 90%+ | Unitário com mock |
| `commands/` | 70%+ | Unitário (helpers) + Integração |
| `reporter/` | 70%+ | Unitário (template render) |

### Estrutura de testes

```
tests/
├── __init__.py
├── conftest.py              # Fixtures compartilhadas (temp_config_file, etc.)
├── test_engine.py           # parse_check, evaluate_check, check_all, get_summary
├── test_client.py           # _extract_json_from_response, error handling
├── test_validate.py         # safe_pct, clean_path, _v_or_none, _build_project_data
├── test_xlsx_extractor.py   # _polygon_area
├── test_project_pdf.py      # extract_dimensions_from_text
├── test_extract_rules.py    # _sanitize_filename
└── test_config.py           # load_config
```

---

## Workflow de Desenvolvimento

### 1. Antes de começar

```bash
git pull origin main
source venv/bin/activate
python3 -m pytest tests/ -v  # confirma que tudo passa antes de mexer
```

### 2. Durante o desenvolvimento

- Commits atômicos: um commit = uma mudança lógica
- Mensagens em conventional commits: `feat:`, `fix:`, `refactor:`, `test:`, `docs:`, `chore:`
- Mantenha funções ≤ 50 linhas e complexidade ≤ 10
- Use type hints em todas as funções públicas
- Prefira `match/case` (Python 3.10+) a longas cadeias `if/elif`
- Use `pathlib.Path`, não `os.path`
- Use f-strings, não `.format()` ou `%`

### 3. Antes do commit

1. **Gate 0 (Instalador):** Revise `install.sh` e `install.ps1` — sua mudança quebrou algo neles?
2. Rode o **Gate 1** (code-review). Resolva tudo ≥ medium.
3. Rode o **Gate 2** (security scanner). Zero high/critical.
4. Rode o **Gate 3** (test suite). 100% passando.
5. Revise o `git diff --staged` — sem arquivos acidentais (`.coverage`, `__pycache__`, etc.)

### 4. Push

```bash
git push origin main
```

**Nunca usar `--force` ou `--force-with-lease`.** Se houver conflito, resolver com merge/rebase normal.

---

## Convenções do Projeto

### Stack

| Componente | Tecnologia |
|-----------|-----------|
| Linguagem | Python 3.11+ |
| CLI framework | Click 8.1+ |
| Output | Rich (tabelas, painéis, prompts) |
| PDF parsing | PyMuPDF (fitz) |
| XLSX parsing | OpenPyXL |
| LLM | OpenAI client (OpenRouter / DeepSeek) |
| HTML reports | Jinja2 |
| Git integration | GitPython |
| Config | YAML (PyYAML) |

### Estrutura de diretórios

```
cli-civileng/
├── cli_civileng/
│   ├── checker/          # Motor de validação (puro, sem I/O)
│   ├── commands/         # Comandos CLI (Click + Rich)
│   ├── extractors/       # Parsers de PDF e XLSX
│   ├── llm/              # Cliente LLM (OpenAI-compatible)
│   └── reporter/         # Gerador de relatórios HTML
├── data/rules/           # JSONs de regras (git-versionados)
├── projects/             # Projetos de clientes (git-ignorados)
├── tests/                # Testes pytest
├── AGENTS.md             # Este arquivo
├── config.yaml.example   # Template de configuração
├── pyproject.toml        # Metadados e dependências
├── setup.sh / setup.bat  # Instalação self-contained
└── .gitignore
```

### Princípios de design

- **Separação I/O de lógica pura** — `checker/` e helpers de `extractors/` não fazem I/O, facilitando testes
- **Python 3.10+ idioms** — `X | None`, `match/case`, `list[dict]`
- **Português na interface**, inglês no código
- **Valor 0 = "não informado"** — nunca assumir que zero é um valor real

### Provider LLM

O projeto suporta OpenRouter e DeepSeek via config. O `api_key` **nunca** vai hardcoded — sempre via `config.yaml` (git-ignored) ou variável de ambiente.

---

## Referências Rápidas

| Comando | O que faz |
|---------|-----------|
| `cli-civileng extract-rules` | PDF de normas → JSON (via LLM) |
| `cli-civileng validate` | XLSX + dados → relatório HTML |
| `python3 -m pytest tests/ -v` | Rodar todos os testes |
| `python3 -m pytest tests/test_engine.py -v` | Rodar testes de um módulo |
| `python3 -m pytest tests/ --cov=cli_civileng --cov-report=term` | Testes com cobertura |

### Skills do Claude Code usadas neste projeto

| Skill | Uso | Quando |
|-------|-----|--------|
| `claudecode-code-reviewer` | Code quality + PR analysis | Pre-push, code review |
| `claudecode-senior-security` | Secret scan + threat model | Pre-push, novas features |
| `claudecode-tdd-guide` | Geração de testes, cobertura | Novos módulos, TDD |
| `github-repo-management` | Criar repo, releases, secrets | Setup inicial, releases |
