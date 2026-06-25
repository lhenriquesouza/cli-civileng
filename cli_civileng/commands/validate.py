"""validate: XLSX + PDF opcional + JSON regras → relatório HTML."""
import json
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

console = Console()
DATA_DIR = Path("data/rules")
PROJECTS_DIR = Path("projects")


def safe_pct(part: float, total: float) -> float:
    """Calculate percentage safely."""
    if total == 0:
        return 0.0
    return round(part / total * 100, 1)


def clean_path(raw: str) -> str:
    """Clean user-provided path: strip quotes, whitespace, expand ~."""
    path = raw.strip().strip("'\"") .strip()
    if not path:
        return ""
    return str(Path(path).expanduser().resolve())


def validate_command():
    """Interactive guided project validation."""
    console.print()
    console.print(
        Panel.fit(
            "[bold green]🔍 Validate Project[/bold green]\n"
            "Valida um projeto (XLSX + PDF opcional) contra regras (JSON) e gera relatório HTML.",
            border_style="green",
        )
    )

    # Step 1: Select rules
    rules_files = sorted(DATA_DIR.glob("*.json"))
    if not rules_files:
        console.print(
            "[red]❌ Nenhum arquivo de regras encontrado em data/rules/[/red]"
        )
        console.print("   Execute [bold]cli-civileng extract-rules[/bold] primeiro.")
        return

    console.print("\n📚 Regras disponíveis:")
    for i, f in enumerate(rules_files, 1):
        try:
            data = json.loads(f.read_text())
            console.print(
                f"  {i}. {data['name']} ({data['type']}) — {len(data.get('rules', []))} regras"
            )
        except Exception:
            console.print(f"  {i}. {f.stem} (erro ao ler)")

    choice = Prompt.ask("Escolha o número da regra", default="1")
    rules_file = rules_files[int(choice) - 1]
    rules = json.loads(rules_file.read_text())

    # Step 2: Client name
    client_name = Prompt.ask("👤 Nome do cliente")

    # Step 2.5: Project name
    project_label = Prompt.ask("📝 Nome do projeto", default="projeto")

    # Step 3: XLSX path
    xlsx_path = clean_path(Prompt.ask("📊 Caminho do arquivo XLSX do projeto"))

    if not Path(xlsx_path).exists():
        console.print(f"[red]❌ Arquivo não encontrado: {xlsx_path}[/red]")
        return

    # Step 4: Extract XLSX data early (needed for defaults)
    console.print("\n📊 Extraindo dados do XLSX...")
    xlsx_data = extract_project_data(xlsx_path)

    # Step 5: Optional PDF of project plans/memorial
    pdf_raw = Prompt.ask(
        "\n📄 PDF da planta/memorial descritivo (Enter para pular)",
        default="",
    )
    pdf_path = clean_path(pdf_raw) if pdf_raw.strip() else ""

    extracted = {}
    if pdf_path.strip():
        pdf_file = Path(pdf_path.strip())
        if pdf_file.exists():
            console.print("🔍 Extraindo dimensões do PDF...")
            text = extract_text(str(pdf_file))
            extracted = extract_dimensions_from_text(text)
            if extracted:
                console.print("   ✅ Dados encontrados no PDF:")
                for k, v in extracted.items():
                    console.print(f"      {k}: {v}")
            else:
                console.print("   ⚠️  Nenhum dado numérico encontrado no PDF")
        else:
            console.print(f"[yellow]⚠️  PDF não encontrado: {pdf_path}[/yellow]")

    # Step 6: Supplementary data (pre-filled from PDF and XLSX when available)
    console.print("\n📐 Dados complementares do terreno")
    console.print("   [green]🟢 verde[/green] = extraído do PDF/XLSX   [yellow]🟡 amarelo[/yellow] = não encontrado, precisa digitar")

    def ask_or_default(prompt_text: str, key: str, xlsx_key: str | None = None, default: str = "0") -> str:
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

    lot_area = ask_or_default("Área do lote (m²)", "lot_area")
    permeable_area = ask_or_default("Área permeável (m²)", "permeable_area")
    building_footprint = ask_or_default(
        "Área de projeção da edificação (m²)",
        "building_footprint",
        xlsx_key="building_footprint_area",
    )
    total_built_area = ask_or_default(
        "Área total construída (m²)",
        "total_built_area",
        xlsx_key="floor_areas_total",
    )
    front_setback = ask_or_default("Recuo frontal (m)", "front_setback")
    back_setback = ask_or_default("Recuo de fundo (m)", "back_setback")
    max_height = ask_or_default(
        "Altura máxima da edificação (m)",
        "max_height",
        xlsx_key="max_height",
    )

    # Step 7: Merge XLSX data with supplementary data
    # Fields with value 0 mean "not provided" → treat as None
    def v_or_none(val: str) -> float | None:
        f = float(val)
        return None if f == 0.0 else f

    _lot = v_or_none(lot_area)
    _perm = v_or_none(permeable_area)
    _footprint = v_or_none(building_footprint)
    _built = v_or_none(total_built_area)
    _front = v_or_none(front_setback)
    _back = v_or_none(back_setback)
    _height = v_or_none(max_height)
    if _height is None:
        _height = xlsx_data.get("max_height", 0)
        if _height == 0:
            _height = None

    project_data = {
        "area_permeavel_pct": safe_pct(_perm or 0, _lot or 0) if _lot and _perm else None,
        "taxa_ocupacao_pct": safe_pct(_footprint or 0, _lot or 0) if _lot and _footprint else None,
        "area_total_construida": _built,
        "recuo_frontal": _front,
        "recuo_fundo": _back,
        "recuo_lateral": None,
        "altura_maxima": _height,
        "altura_terreno_pnt": None,
        "area_edicula_pct": None,
        "afastamento_glp": None,
    }

    # Step 8: Run checks
    console.print("\n🔍 Executando verificações...")
    results = check_all(project_data, rules["rules"])
    summary = get_summary(results)

    # Step 9: Display summary
    table = Table(title="Resultado")
    table.add_column("Status", style="bold")
    table.add_column("Regra")
    table.add_column("Detalhe")

    for r in results:
        status = "✅" if r["passed"] else ("⚠️" if r["actual"] is None else "❌")
        table.add_row(status, r["name"], r["message"])

    console.print(table)

    # Step 10: Save report
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
    output_path = generate_report(
        results, summary, project_name, rules["name"], str(report_path)
    )

    console.print(f"\n✅ Relatório salvo em: [green]{output_path}[/green]")
    console.print()
