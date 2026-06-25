"""Generate HTML compliance reports."""
from pathlib import Path
from datetime import datetime

from jinja2 import Environment, FileSystemLoader

TEMPLATE_DIR = Path(__file__).parent / "templates"


def generate_report(
    results: list[dict],
    summary: dict,
    project_name: str,
    rule_set_name: str,
    output_path: str,
) -> str:
    """Generate an HTML report from check results."""
    env = Environment(loader=FileSystemLoader(str(TEMPLATE_DIR)))
    template = env.get_template("report.html.j2")

    html = template.render(
        results=results,
        summary=summary,
        project_name=project_name,
        rule_set_name=rule_set_name,
        date=datetime.now().strftime("%d/%m/%Y %H:%M"),
    )

    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(html, encoding="utf-8")

    return str(path)
