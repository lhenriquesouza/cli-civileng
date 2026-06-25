"""Tests for checker/engine.py — pure logic functions."""
import pytest
from cli_civileng.checker.engine import (
    parse_check,
    evaluate_check,
    check_all,
    get_summary,
)


class TestParseCheck:
    def test_valid_three_parts(self):
        var, op, val = parse_check("area_permeavel_pct >= 20")
        assert var == "area_permeavel_pct"
        assert op == ">="
        assert val == 20.0

    def test_valid_with_decimal(self):
        var, op, val = parse_check("recuo_fundo <= 3.5")
        assert var == "recuo_fundo"
        assert op == "<="
        assert val == 3.5

    def test_invalid_format_raises(self):
        with pytest.raises(ValueError, match="Invalid check format"):
            parse_check("only_one_token")

    def test_invalid_two_parts_raises(self):
        with pytest.raises(ValueError, match="Invalid check format"):
            parse_check("area >= ")


class TestEvaluateCheck:
    def test_gte_passes(self):
        passed, actual, msg = evaluate_check(
            "area", ">=", 20, {"area": 25}
        )
        assert passed is True
        assert actual == 25.0
        assert "Conforme" in msg

    def test_gte_fails(self):
        passed, actual, msg = evaluate_check(
            "area", ">=", 20, {"area": 15}
        )
        assert passed is False
        assert actual == 15.0
        assert "Não conforme" in msg

    def test_lte_passes(self):
        passed, _, _ = evaluate_check(
            "height", "<=", 10, {"height": 8}
        )
        assert passed is True

    def test_lte_fails(self):
        passed, _, _ = evaluate_check(
            "height", "<=", 10, {"height": 12}
        )
        assert passed is False

    def test_gt_passes(self):
        passed, _, _ = evaluate_check(
            "area", ">", 10, {"area": 15}
        )
        assert passed is True

    def test_gt_fails_equal(self):
        passed, _, _ = evaluate_check(
            "area", ">", 10, {"area": 10}
        )
        assert passed is False

    def test_lt_passes(self):
        passed, _, _ = evaluate_check(
            "area", "<", 10, {"area": 5}
        )
        assert passed is True

    def test_eq_passes(self):
        passed, _, _ = evaluate_check(
            "area", "==", 10, {"area": 10}
        )
        assert passed is True

    def test_eq_passes_within_tolerance(self):
        passed, _, _ = evaluate_check(
            "area", "==", 10, {"area": 10.005}
        )
        assert passed is True

    def test_eq_fails(self):
        passed, _, _ = evaluate_check(
            "area", "==", 10, {"area": 10.02}
        )
        assert passed is False

    def test_missing_data(self):
        passed, actual, msg = evaluate_check(
            "area", ">=", 20, {}
        )
        assert passed is False
        assert actual is None
        assert "não disponível" in msg

    def test_none_value(self):
        passed, actual, msg = evaluate_check(
            "area", ">=", 20, {"area": None}
        )
        assert passed is False
        assert actual is None

    def test_invalid_value_type(self):
        passed, actual, msg = evaluate_check(
            "area", ">=", 20, {"area": "abc"}
        )
        assert passed is False
        assert actual is None
        assert "inválido" in msg.lower() or "Valor inválido" in msg

    def test_unknown_operator(self):
        passed, actual, msg = evaluate_check(
            "area", "!=", 20, {"area": 25}
        )
        assert passed is False
        assert "desconhecido" in msg.lower()


class TestCheckAll:
    def test_all_pass(self):
        rules = [
            {"id": "R01", "check": "area >= 20", "name": "Min area"},
            {"id": "R02", "check": "height <= 10", "name": "Max height"},
        ]
        data = {"area": 25, "height": 8}
        results = check_all(data, rules)
        assert len(results) == 2
        assert all(r["passed"] for r in results)

    def test_one_fails(self):
        rules = [
            {"id": "R01", "check": "area >= 20", "name": "Min area"},
            {"id": "R02", "check": "height <= 10", "name": "Max height"},
        ]
        data = {"area": 15, "height": 8}
        results = check_all(data, rules)
        assert results[0]["passed"] is False
        assert results[1]["passed"] is True

    def test_missing_data_marks_failed(self):
        rules = [
            {"id": "R01", "check": "missing_var >= 20", "name": "Missing"},
        ]
        data = {}
        results = check_all(data, rules)
        assert results[0]["passed"] is False
        assert results[0]["actual"] is None

    def test_invalid_check_format(self):
        rules = [
            {"id": "R01", "check": "bad_format", "name": "Bad"},
        ]
        results = check_all({}, rules)
        assert results[0]["passed"] is False
        assert "Invalid check format" in results[0]["message"]

    def test_suggestion_on_failure(self):
        rules = [
            {"id": "R01", "check": "area >= 20", "name": "Min area"},
        ]
        data = {"area": 15}
        results = check_all(data, rules)
        assert results[0]["suggestion"] != ""


class TestGetSummary:
    def test_all_passed(self):
        results = [
            {"passed": True, "actual": 25},
            {"passed": True, "actual": 8},
        ]
        summary = get_summary(results)
        assert summary["total"] == 2
        assert summary["passed"] == 2
        assert summary["failed"] == 0
        assert summary["unchecked"] == 0
        assert summary["pass_rate"] == 100.0

    def test_mixed_results(self):
        results = [
            {"passed": True, "actual": 25},
            {"passed": False, "actual": 15},
            {"passed": False, "actual": None},
        ]
        summary = get_summary(results)
        assert summary["total"] == 3
        assert summary["passed"] == 1
        assert summary["failed"] == 1
        assert summary["unchecked"] == 1
        assert summary["pass_rate"] == pytest.approx(33.3, rel=0.1)

    def test_empty_results(self):
        summary = get_summary([])
        assert summary["total"] == 0
        assert summary["pass_rate"] == 0
