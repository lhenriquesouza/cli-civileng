"""Tests for commands/validate.py helper functions."""
import pytest
from cli_civileng.commands.validate import (
    safe_pct,
    clean_path,
    _v_or_none,
    _build_project_data,
)


class TestSafePct:
    def test_normal_case(self):
        assert safe_pct(50, 200) == 25.0

    def test_zero_total(self):
        assert safe_pct(10, 0) == 0.0

    def test_hundred_percent(self):
        assert safe_pct(100, 100) == 100.0

    def test_rounding(self):
        result = safe_pct(1, 3)
        assert result == 33.3  # 1/3 * 100 = 33.333... -> 33.3

    def test_zero_part(self):
        assert safe_pct(0, 100) == 0.0


class TestCleanPath:
    def test_strips_quotes(self):
        result = clean_path('"/home/user/file.xlsx"')
        assert not result.startswith('"')
        assert not result.endswith('"')

    def test_strips_single_quotes(self):
        result = clean_path("'/home/user/file.xlsx'")
        assert not result.startswith("'")

    def test_strips_whitespace(self):
        result = clean_path("  /home/user/file.xlsx  ")
        assert result.startswith("/home")

    def test_empty_string(self):
        assert clean_path("") == ""

    def test_expands_tilde(self):
        result = clean_path("~/documents")
        assert not result.startswith("~")


class TestVOrNone:
    def test_positive_value(self):
        assert _v_or_none("25.5") == 25.5

    def test_zero_returns_none(self):
        assert _v_or_none("0") is None

    def test_zero_as_float(self):
        assert _v_or_none("0.0") is None

    def test_value_with_negative(self):
        assert _v_or_none("-1") == -1.0


class TestBuildProjectData:
    def test_all_provided(self):
        inputs = {
            "lot_area": "200",
            "permeable_area": "40",
            "building_footprint": "100",
            "total_built_area": "300",
            "front_setback": "5",
            "back_setback": "3",
            "max_height": "10",
        }
        data = _build_project_data(inputs, {})
        assert data["area_permeavel_pct"] == 20.0
        assert data["taxa_ocupacao_pct"] == 50.0
        assert data["area_total_construida"] == 300.0
        assert data["recuo_frontal"] == 5.0
        assert data["recuo_fundo"] == 3.0
        assert data["altura_maxima"] == 10.0

    def test_missing_lot_returns_none_pcts(self):
        inputs = {
            "lot_area": "0",
            "permeable_area": "40",
            "building_footprint": "100",
            "total_built_area": "300",
            "front_setback": "5",
            "back_setback": "3",
            "max_height": "10",
        }
        data = _build_project_data(inputs, {})
        # lot_area is 0 → _v_or_none returns None
        assert data["area_permeavel_pct"] is None
        assert data["taxa_ocupacao_pct"] is None

    def test_height_from_xlsx_fallback(self):
        inputs = {
            "lot_area": "200",
            "permeable_area": "40",
            "building_footprint": "100",
            "total_built_area": "300",
            "front_setback": "5",
            "back_setback": "3",
            "max_height": "0",
        }
        xlsx_data = {"max_height": 8.5}
        data = _build_project_data(inputs, xlsx_data)
        assert data["altura_maxima"] == 8.5

    def test_unavailable_fields_are_none(self):
        inputs = {
            "lot_area": "200",
            "permeable_area": "40",
            "building_footprint": "100",
            "total_built_area": "300",
            "front_setback": "5",
            "back_setback": "3",
            "max_height": "10",
        }
        data = _build_project_data(inputs, {})
        assert data["recuo_lateral"] is None
        assert data["altura_terreno_pnt"] is None
        assert data["area_edicula_pct"] is None
        assert data["afastamento_glp"] is None
