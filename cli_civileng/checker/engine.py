"""Compliance checker — compares project data against rules."""
import re
from typing import Any

PERCENT_MULTIPLIER = 100


def parse_check(check_str: str) -> tuple[str, str, float]:
    """Parse a check string like 'area_permeavel_pct >= 20' into (var, op, value)."""
    parts = check_str.strip().split()
    if len(parts) == 3:
        return parts[0], parts[1], float(parts[2])
    raise ValueError(f"Invalid check format: {check_str}")


def evaluate_check(
    var_name: str, operator: str, expected: float, data: dict
) -> tuple[bool, float | None, str]:
    """Evaluate a single rule check against project data.

    Returns (passed: bool, actual_value: float | None, message: str).
    """
    actual = data.get(var_name)

    if actual is None:
        return False, None, f"Dado '{var_name}' não disponível no projeto"

    try:
        actual = float(actual)
    except (TypeError, ValueError):
        return False, None, f"Valor inválido para '{var_name}': {actual}"

    match operator:
        case ">=":
            passed = actual >= expected
        case "<=":
            passed = actual <= expected
        case ">":
            passed = actual > expected
        case "<":
            passed = actual < expected
        case "==":
            passed = abs(actual - expected) < 0.01
        case _:
            return False, actual, f"Operador desconhecido: {operator}"

    if passed:
        msg = "✅ Conforme"
    else:
        direction = "aumentar" if operator in (">=", ">") else "reduzir"
        diff = abs(actual - expected)
        msg = f"❌ Não conforme — sugere-se {direction} em {diff:.2f}"

    return passed, actual, msg


def check_all(data: dict, rules: list[dict]) -> list[dict]:
    """Run all rules against project data.

    Returns list of results with: rule, passed, actual, expected, message, suggestion.
    """
    results: list[dict] = []
    for rule in rules:
        try:
            var, op, expected = parse_check(rule["check"])
        except ValueError as e:
            results.append(
                {
                    **rule,
                    "passed": False,
                    "actual": None,
                    "expected": None,
                    "message": str(e),
                    "suggestion": "",
                }
            )
            continue

        passed, actual, message = evaluate_check(var, op, expected, data)

        suggestion = ""
        if not passed and actual is not None:
            diff = abs(actual - expected)
            suggestion = (
                f"Encontrado: {actual:.2f} | Exigido: {expected:.2f} "
                f"| Ajuste necessário: {diff:.2f}"
            )

        results.append(
            {
                **rule,
                "passed": passed,
                "actual": actual,
                "expected_value": f"{expected} {rule.get('unit', '')}",
                "message": message,
                "suggestion": suggestion,
            }
        )

    return results


def get_summary(results: list[dict]) -> dict[str, int | float]:
    """Generate summary statistics."""
    total = len(results)
    passed = sum(1 for r in results if r["passed"])
    failed = sum(
        1 for r in results if not r["passed"] and r["actual"] is not None
    )
    unchecked = sum(1 for r in results if r["actual"] is None)

    return {
        "total": total,
        "passed": passed,
        "failed": failed,
        "unchecked": unchecked,
        "pass_rate": round(passed / total * PERCENT_MULTIPLIER, 1) if total > 0 else 0,
    }
