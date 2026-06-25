# CLI CivilEng

Ferramenta CLI para verificação de conformidade de projetos de engenharia civil contra normas de condomínios e municípios.

## Instalação

### Linux

```bash
git clone <repo-url>
cd cli-civileng
bash setup.sh
source venv/bin/activate
```

### Windows

```bat
git clone <repo-url>
cd cli-civileng
setup.bat
venv\Scripts\activate.bat
```

### Configurar API Key

```bash
cp config.yaml.example config.yaml
# Edite config.yaml com sua chave de API OpenRouter
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

O JSON gerado é salvo em `data/rules/` e versionado com git.

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
cli-civileng/
├── data/rules/           # JSONs de regras (um por condomínio/município)
├── projects/             # Um diretório por cliente
│   └── <cliente>/
│       └── <condominio>/
│           └── <projeto>/
│               ├── projeto.xlsx
│               ├── dados_terreno.json
│               └── reports/
│                   └── 2026-06-24_20h55.html
├── config.yaml           # Configuração LLM (api_key, provider, model)
├── setup.sh / setup.bat  # Instalação self-contained
└── cli_civileng/         # Código fonte
```

## Formatos suportados

- **Projeto:** XLSX no formato SAF (Structural Analysis Format) exportado do ArchiCAD
- **Normas:** PDF (extração via LLM → JSON) ou JSON manual
- **Relatório:** HTML auto-contido, imprimível

## Stack

Python 3.11+ • Click • Rich • PyMuPDF • OpenPyXL • OpenAI • Jinja2 • GitPython
