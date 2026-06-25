"""Tests for extractors/xlsx_extractor.py."""
import pytest
from cli_civileng.extractors.xlsx_extractor import _polygon_area


class TestPolygonArea:
    def test_triangle(self):
        coords = [(0, 0, 0), (3, 0, 0), (0, 4, 0)]
        area = _polygon_area(coords)
        assert area == pytest.approx(6.0)  # 3×4 / 2

    def test_square(self):
        coords = [(0, 0, 0), (2, 0, 0), (2, 2, 0), (0, 2, 0)]
        area = _polygon_area(coords)
        assert area == pytest.approx(4.0)

    def test_rectangle(self):
        coords = [(0, 0, 0), (5, 0, 0), (5, 3, 0), (0, 3, 0)]
        area = _polygon_area(coords)
        assert area == pytest.approx(15.0)

    def test_less_than_three_points(self):
        assert _polygon_area([(0, 0, 0), (1, 1, 0)]) == 0.0

    def test_empty_coords(self):
        assert _polygon_area([]) == 0.0

    def test_ignores_z(self):
        coords_flat = [(0, 0, 0), (4, 0, 0), (4, 3, 0), (0, 3, 0)]
        coords_raised = [(0, 0, 10), (4, 0, 10), (4, 3, 10), (0, 3, 10)]
        assert _polygon_area(coords_flat) == _polygon_area(coords_raised)
