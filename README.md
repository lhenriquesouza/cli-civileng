# CLI CivilEng

Ferramenta CLI para verificação de conformidade de projetos de engenharia civil contra normas de condomínios e municípios.

## Instalação

### Linux / macOS

```bash
curl -fsSL https://raw.githubusercontent.com/lhenriquesouza/cli-civileng/main/install.sh | bash
```

### Windows (PowerShell)

```powershell
irm https://raw.githubusercontent.com/lhenriquesouza/cli-civileng/main/install.ps1 | iex
```

O script instala em `~/.cli-civileng/` (ou `%USERPROFILE%\.cli-civileng` no Windows), cria um venv isolado, e adiciona o comando `cli-civileng` ao seu PATH.

> 💡 **Dica de segurança:** Se preferir revisar antes de executar:
>
> **Linux/macOS:**
> ```bash
> curl -fsSL https://raw.githubusercontent.com/lhenriquesouza/cli-civileng/main/install.sh -o install.sh
> less install.sh   # revise o código
> bash install.sh
> ```
>
> **Windows:**
> ```powershell
> irm https://raw.githubusercontent.com/lhenriquesouza/cli-civileng/main/install.ps1 -OutFile install.ps1
> notepad install.ps1   # revise o código
> .\install.ps1
> ```

### Configurar API Key

```bash
# O install.sh já cria o config.yaml pra você. Se instalou manualmente:
cp config.yaml.example config.yaml
# Edite config.yaml com sua chave de API OpenRouter/DeepSeek
```

## Uso

### Extrair regras de um PDF de normas

```bash
cli-civileng extract-rules
```

O comando guia interativamente:
1. Caminho do PDF de normas
2. Tipo (condomínio ou município)
3. Nome da norma

O JSON gerado é salvo em `~/.cli-civileng/data/rules/` e versionado com git.

### Validar um projeto

```bash
cli-civileng validate
```

O comando guia interativamente:
1. Seleção das regras (JSON)
2. Nome do cliente
3. Caminho do XLSX do projeto (exportado do ArchiCAD)
4. Dados complementares do terreno (área do lote, permeável, recuos, etc.)

O relatório HTML é salvo em `projects/<cliente>/<condominio>/reports/`.

## Estrutura de diretórios

```
~/.cli-civileng/
├── data/rules/           # JSONs de regras (um por condomínio/município)
├── projects/             # Um diretório por cliente
│   └── <cliente>/
│       └── <condominio>/
│           └── <projeto>/
│               ├── projeto.xlsx
│               └── reports/
│                   └── 2026-06-24_20h55.html
├── config.yaml           # Configuração LLM (api_key, provider, model)
└── venv/                 # Ambiente virtual isolado
```

## Formatos suportados

- **Projeto:** XLSX no formato SAF (Structural Analysis Format) exportado do ArchiCAD
- **Normas:** PDF (extração via LLM → JSON) ou JSON manual
- **Relatório:** HTML auto-contido, imprimível

## Desenvolvimento

Veja [AGENTS.md](AGENTS.md) para o checklist de pre-push, política de testes e convenções do projeto.

## Stack

Python 3.11+ • Click • Rich • PyMuPDF • OpenPyXL • OpenAI • Jinja2 • GitPython
