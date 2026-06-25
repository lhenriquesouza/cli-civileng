"""CLI CivilEng — Verificação de conformidade de projetos civis."""
import click

from cli_civileng.commands.extract_rules import extract_rules_command
from cli_civileng.commands.validate import validate_command


@click.group()
@click.version_option(version="0.1.0")
def cli():
    """CLI CivilEng — Extraia regras de normas e valide projetos."""
    pass


@cli.command()
def extract_rules():
    """Extrai regras de um PDF de normas para JSON estruturado (via LLM)."""
    extract_rules_command()


@cli.command()
def validate():
    """Valida um projeto (XLSX) contra regras (JSON) e gera relatório HTML."""
    validate_command()


if __name__ == "__main__":
    cli()
