"""extract-rules: PDF de normas → JSON estruturado via LLM."""
import json
import logging
from pathlib import Path
from datetime import datetime

import click
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt

from cli_civileng.extractors.pdf_extractor import extract_text
from cli_civileng.llm.client import extract_rules_from_text

logger = logging.getLogger(__name__)
console = Console()
RULES_DIR = Path("data/rules")


def _sanitize_filename(name: str) -> str:
    """Convert a name to a safe filename slug."""
    replacements = {
        "ç": "c", "ã": "a", "á": "a", "é": "e",
        "í": "i", "ó": "o", "ú": "u", " ": "-",
    }
    result = name.lower()
    for old, new in replacements.items():
        result = result.replace(old, new)
    return result


def _git_add_and_commit(output_path: Path, rule_name: str, rule_type: str) -> None:
    """Attempt to git-add and commit the generated rules file."""
    try:
        import git

        repo = git.Repo(".", search_parent_directories=True)
        repo.index.add([str(output_path)])
        repo.index.commit(f"feat: add rules for {rule_name} ({rule_type})")
        console.print("   📦 Versionado com git")
    except git.InvalidGitRepositoryError:
        console.print(
            "   ⚠️  Diretório não é um repositório git — pulando versionamento"
        )
    except Exception as e:
        logger.warning("Git versioning failed: %s", e)
        console.print(f"   ⚠️  Erro ao versionar com git: {e}")


def extract_rules_command() -> None:
    """Interactive guided extraction of rules from PDF."""
    console.print()
    console.print(
        Panel.fit(
            "[bold blue]📋 Extract Rules[/bold blue]\n"
            "Extrai regras de um PDF de normas para JSON estruturado.\n"
            "O JSON gerado será versionado automaticamente com git.",
            border_style="blue",
        )
    )

    # Step 1: PDF path
    pdf_path = Prompt.ask("\n📄 Caminho do arquivo PDF de normas")
    pdf_file = Path(pdf_path)
    if not pdf_file.exists():
        console.print(f"[red]❌ Arquivo não encontrado: {pdf_path}[/red]")
        return

    # Step 2: Norma type
    rule_type = Prompt.ask(
        "🏷️  Tipo de norma",
        choices=["condominium", "municipality"],
        default="condominium",
    )

    # Step 3: Norma name
    rule_name = Prompt.ask(
        "📛 Nome da norma/condomínio/município", default=pdf_file.stem
    )

    # Step 4: Extract text
    console.print("\n🔍 Extraindo texto do PDF...")
    text = extract_text(str(pdf_file))

    if len(text) < 10:
        console.print("[red]❌ PDF vazio ou ilegível.[/red]")
        return

    console.print(f"   ✅ {len(text):,} caracteres extraídos")

    # Step 5: Send to LLM
    console.print("\n🤖 Enviando para LLM extrair regras...")
    try:
        rules_json = extract_rules_from_text(text)
    except (ValueError, ConnectionError, OSError) as e:
        logger.error("LLM extraction failed: %s", e)
        console.print(f"[red]❌ Erro na LLM: {e}[/red]")
        return

    # Step 6: Save JSON
    RULES_DIR.mkdir(parents=True, exist_ok=True)
    output_name = _sanitize_filename(rule_name)
    output_path = RULES_DIR / f"{output_name}.json"

    rules_json["name"] = rule_name
    rules_json["type"] = rule_type
    rules_json["extracted_at"] = datetime.now().isoformat()
    rules_json["source_pdf"] = pdf_file.name

    output_path.write_text(
        json.dumps(rules_json, indent=2, ensure_ascii=False), encoding="utf-8"
    )

    console.print(f"\n✅ Regras salvas em: [green]{output_path}[/green]")
    console.print(f"   📊 {len(rules_json.get('rules', []))} regras extraídas")

    # Step 7: Git versioning
    _git_add_and_commit(output_path, rule_name, rule_type)

    console.print()
