"""Tests for extractors/project_pdf_extractor.py."""
from cli_civileng.extractors.project_pdf_extractor import extract_dimensions_from_text


class TestExtractDimensionsFromText:
    def test_permeable_area(self):
        text = "ÁREA PERMEÁVEL TOTAL = 75,5 m²"
        result = extract_dimensions_from_text(text)
        assert result["permeable_area"] == 75.5

    def test_lot_area(self):
        text = "Área do lote = 250,00 m²"
        result = extract_dimensions_from_text(text)
        assert result["lot_area"] == 250.0

    def test_total_built_area(self):
        text = "Área total construída = 180,5 m²"
        result = extract_dimensions_from_text(text)
        assert result["total_built_area"] == 180.5

    def test_front_setback(self):
        text = "Recuo frontal = 5,00 m"
        result = extract_dimensions_from_text(text)
        assert result["front_setback"] == 5.0

    def test_back_setback(self):
        text = "Recuo de fundos = 3,50 m"
        result = extract_dimensions_from_text(text)
        assert result["back_setback"] == 3.5

    def test_max_height(self):
        text = "Altura máxima da edificação = 9,00 m"
        result = extract_dimensions_from_text(text)
        assert result["max_height"] == 9.0

    def test_building_footprint(self):
        text = "Área de projeção = 120,00 m²"
        result = extract_dimensions_from_text(text)
        assert result["building_footprint"] == 120.0

    def test_lot_dimensions_calculates_area(self):
        text = "25,00 x 10,00 m"
        result = extract_dimensions_from_text(text)
        assert result["lot_area"] == 250.0

    def test_lot_dimensions_with_X(self):
        text = "30,00 X 20,00 m"
        result = extract_dimensions_from_text(text)
        assert result["lot_area"] == 600.0

    def test_lot_dimensions_with_multiplication_sign(self):
        text = "15,5 × 8,0 m"
        result = extract_dimensions_from_text(text)
        assert result["lot_area"] == 124.0

    def test_multiple_patterns(self):
        text = """
        Área do lote = 300,00 m²
        ÁREA PERMEÁVEL TOTAL = 60,00 m²
        Recuo frontal = 5,00 m
        Altura máxima = 7,50 m
        """
        result = extract_dimensions_from_text(text)
        assert result["lot_area"] == 300.0
        assert result["permeable_area"] == 60.0
        assert result["front_setback"] == 5.0
        assert result["max_height"] == 7.5

    def test_empty_text(self):
        result = extract_dimensions_from_text("")
        assert result == {}

    def test_no_matches(self):
        result = extract_dimensions_from_text("Lorem ipsum dolor sit amet")
        assert result == {}

    def test_case_insensitive(self):
        text = "área do lote = 200,00 m²"
        result = extract_dimensions_from_text(text)
        assert result["lot_area"] == 200.0

    def test_permeable_preferred_over_alt(self):
        text = "ÁREA PERMEÁVEL TOTAL = 50,0 m²\nTOTAL\n25,0"
        result = extract_dimensions_from_text(text)
        assert result["permeable_area"] == 50.0

    def test_permeable_alt_as_fallback(self):
        text = "TOTAL\n35,0"
        result = extract_dimensions_from_text(text)
        assert result.get("permeable_area") == 35.0
