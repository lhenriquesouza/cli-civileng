"""validate: XLSX + PDF opcional + JSON regras → relatório HTML."""
import json
import logging
from pathlib import Path
from datetime import datetime

import click
from rich.console import Console
from rich.prompt import Prompt
from rich.panel import Panel
from rich.table import Table

from cli_civileng.extractors.xlsx_extractor import extract_project_data
from cli_civileng.extractors.project_pdf_extractor import (
    extract_text,
    extract_dimensions_from_text,
)
from cli_civileng.checker.engine import check_all, get_summary
from cli_civileng.reporter.html_reporter import generate_report

logger = logging.getLogger(__name__)
console = Console()

PERCENT_MULTIPLIER = 100
DATA_DIR = Path("data/rules")
PROJECTS_DIR = Path("projects")


def safe_pct(part: float, total: float) -> float:
    """Calculate percentage safely."""
    if total == 0:
        return 0.0
    return round(part / total * PERCENT_MULTIPLIER, 1)


def clean_path(raw: str) -> str:
    """Clean user-provided path: strip quotes, whitespace, expand ~."""
    path = raw.strip().strip("'\"").strip()
    if not path:
        return ""
    return str(Path(path).expanduser().resolve())


def _select_rules() -> dict:
    """Interactive step: select a ruleset from data/rules/."""
    rules_files = sorted(DATA_DIR.glob("*.json"))
    if not rules_files:
        console.print(
            "[red]❌ Nenhum arquivo de regras encontrado em data/rules/[/red]"
        )
        console.print("   Execute [bold]cli-civileng extract-rules[/bold] primeiro.")
        raise SystemExit(1)

    console.print("\n📚 Regras disponíveis:")
    for i, f in enumerate(rules_files, 1):
        try:
            data = json.loads(f.read_text())
            console.print(
                f"  {i}. {data['name']} ({data['type']}) — "
                f"{len(data.get('rules', []))} regras"
            )
        except (json.JSONDecodeError, KeyError) as e:
            logger.warning("Failed to read rules file %s: %s", f, e)
            console.print(f"  {i}. {f.stem} (erro ao ler)")

    choice = Prompt.ask("Escolha o número da regra", default="1")
    rules_file = rules_files[int(choice) - 1]
    return json.loads(rules_file.read_text())


def _extract_pdf_dimensions(pdf_path: str) -> dict:
    """Try to extract dimensions from a project PDF."""
    extracted: dict = {}
    if not pdf_path.strip():
        return extracted

    pdf_file = Path(pdf_path.strip())
    if not pdf_file.exists():
        console.print(f"[yellow]⚠️  PDF não encontrado: {pdf_path}[/yellow]")
        return extracted

    console.print("🔍 Extraindo dimensões do PDF...")
    text = extract_text(str(pdf_file))
    extracted = extract_dimensions_from_text(text)
    if extracted:
        console.print("   ✅ Dados encontrados no PDF:")
        for k, v in extracted.items():
            console.print(f"      {k}: {v}")
    else:
        console.print("   ⚠️  Nenhum dado numérico encontrado no PDF")
    return extracted


def _ask_or_default(
    prompt_text: str,
    key: str,
    xlsx_data: dict,
    extracted: dict,
    xlsx_key: str | None = None,
    default: str = "0",
) -> str:
    """Ask user for a value, pre-filling from PDF/XLSX data when available."""
    d = default
    found = False
    source = ""

    if key in extracted:
        d = str(extracted[key])
        found = True
        source = "PDF"
    elif xlsx_key and xlsx_key in xlsx_data and xlsx_data[xlsx_key]:
        d = str(xlsx_data[xlsx_key])
        found = True
        source = "XLSX"

    if found:
        label = f"   [green]🟢 {prompt_text} [dim]({source}: {d})[/dim][/green]"
    else:
        label = f"   [yellow]🟡 {prompt_text} [dim](não encontrado)[/dim][/yellow]"

    console.print(label)
    return Prompt.ask("   →", default=d)


def _collect_supplementary_data(
    xlsx_data: dict, extracted: dict
) -> dict[str, str]:
    """Collect supplementary project data from user (pre-filled from PDF/XLSX)."""
    console.print("\n📐 Dados complementares do terreno")
    console.print(
        "   [green]🟢 verde[/green] = extraído do PDF/XLSX   "
        "[yellow]🟡 amarelo[/yellow] = não encontrado, precisa digitar"
    )

    return {
        "lot_area": _ask_or_default("Área do lote (m²)", "lot_area", xlsx_data, extracted),
        "permeable_area": _ask_or_default(
            "Área permeável (m²)", "permeable_area", xlsx_data, extracted
        ),
        "building_footprint": _ask_or_default(
            "Área de projeção da edificação (m²)",
            "building_footprint",
            xlsx_data,
            extracted,
            xlsx_key="building_footprint_area",
        ),
        "total_built_area": _ask_or_default(
            "Área total construída (m²)",
            "total_built_area",
            xlsx_data,
            extracted,
            xlsx_key="floor_areas_total",
        ),
        "front_setback": _ask_or_default(
            "Recuo frontal (m)", "front_setback", xlsx_data, extracted
        ),
        "back_setback": _ask_or_default(
            "Recuo de fundo (m)", "back_setback", xlsx_data, extracted
        ),
        "max_height": _ask_or_default(
            "Altura máxima da edificação (m)",
            "max_height",
            xlsx_data,
            extracted,
            xlsx_key="max_height",
        ),
    }


def _v_or_none(val: str) -> float | None:
    """Convert string to float; return None if value is 0 (meaning 'not provided')."""
    f = float(val)
    return None if f == 0.0 else f


def _build_project_data(
    inputs: dict[str, str], xlsx_data: dict
) -> dict:
    """Merge all inputs into the structured project_data dict for checking."""
    _lot = _v_or_none(inputs["lot_area"])
    _perm = _v_or_none(inputs["permeable_area"])
    _footprint = _v_or_none(inputs["building_footprint"])
    _built = _v_or_none(inputs["total_built_area"])
    _front = _v_or_none(inputs["front_setback"])
    _back = _v_or_none(inputs["back_setback"])
    _height = _v_or_none(inputs["max_height"])

    if _height is None:
        _height = xlsx_data.get("max_height", 0)
        if _height == 0:
            _height = None

    return {
        "area_permeavel_pct": (
            safe_pct(_perm or 0, _lot or 0) if _lot and _perm else None
        ),
        "taxa_ocupacao_pct": (
            safe_pct(_footprint or 0, _lot or 0) if _lot and _footprint else None
        ),
        "area_total_construida": _built,
        "recuo_frontal": _front,
        "recuo_fundo": _back,
        "recuo_lateral": None,
        "altura_maxima": _height,
        "altura_terreno_pnt": None,
        "area_edicula_pct": None,
        "afastamento_glp": None,
    }


def _display_results(results: list[dict]) -> None:
    """Display check results in a Rich table."""
    table = Table(title="Resultado")
    table.add_column("Status", style="bold")
    table.add_column("Regra")
    table.add_column("Detalhe")

    for r in results:
        if r["passed"]:
            status = "✅"
        elif r["actual"] is None:
            status = "⚠️"
        else:
            status = "❌"
        table.add_row(status, r["name"], r["message"])

    console.print(table)


def _save_report(
    results: list[dict],
    summary: dict,
    client_name: str,
    project_label: str,
    rules: dict,
) -> str:
    """Generate and save HTML report, return output path."""
    client_dir = (
        PROJECTS_DIR
        / client_name.lower().replace(" ", "-")
        / rules["name"].lower().replace(" ", "-")
        / project_label.lower().replace(" ", "-")
    )
    reports_dir = client_dir / "reports"
    reports_dir.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now().strftime("%Y-%m-%d_%Hh%M")
    report_path = reports_dir / f"{timestamp}.html"

    project_name = f"{client_name} — {project_label} — {rules['name']}"
    return generate_report(
        results, summary, project_name, rules["name"], str(report_path)
    )


def validate_command() -> None:
    """Interactive guided project validation."""
    console.print()
    console.print(
        Panel.fit(
            "[bold green]🔍 Validate Project[/bold green]\n"
            "Valida um projeto (XLSX + PDF opcional) contra regras (JSON) "
            "e gera relatório HTML.",
            border_style="green",
        )
    )

    # Step 1: Select rules
    rules = _select_rules()

    # Step 2: Client name
    client_name = Prompt.ask("👤 Nome do cliente")

    # Step 3: Project name
    project_label = Prompt.ask("📝 Nome do projeto", default="projeto")

    # Step 4: XLSX path
    xlsx_path = clean_path(Prompt.ask("📊 Caminho do arquivo XLSX do projeto"))
    if not Path(xlsx_path).exists():
        console.print(f"[red]❌ Arquivo não encontrado: {xlsx_path}[/red]")
        return

    # Step 5: Extract XLSX data
    console.print("\n📊 Extraindo dados do XLSX...")
    xlsx_data = extract_project_data(xlsx_path)

    # Step 6: Optional PDF
    pdf_raw = Prompt.ask(
        "\n📄 PDF da planta/memorial descritivo (Enter para pular)",
        default="",
    )
    pdf_path = clean_path(pdf_raw) if pdf_raw.strip() else ""
    extracted = _extract_pdf_dimensions(pdf_path)

    # Step 7: Supplementary data
    inputs = _collect_supplementary_data(xlsx_data, extracted)

    # Step 8: Build project data
    project_data = _build_project_data(inputs, xlsx_data)

    # Step 9: Run checks
    console.print("\n🔍 Executando verificações...")
    results = check_all(project_data, rules["rules"])
    summary = get_summary(results)

    # Step 10: Display results
    _display_results(results)

    # Step 11: Save report
    output_path = _save_report(results, summary, client_name, project_label, rules)
    console.print(f"\n✅ Relatório salvo em: [green]{output_path}[/green]")
    console.print()
