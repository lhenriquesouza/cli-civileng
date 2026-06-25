"""Extract project dimensions from memorial/planta PDFs."""
import re


def extract_dimensions_from_text(text: str) -> dict:
    """Try to extract known dimension patterns from project PDF text.

    Returns dict with any found values (keys match what validate needs).
    """
    found = {}

    patterns = [
        # Área permeável total
        (r"(?:ÁREA PERMEÁVEL TOTAL|APT)\s*[=:]\s*([\d,.]+)\s*m²", "permeable_area"),
        # Área do lote / terreno
        (r"(?:Área do lote|Área do terreno|Área total do lote)\s*[=:]\s*([\d,.]+)\s*m²", "lot_area"),
        # Área construída total
        (r"(?:Área (?:total )?construída|Área da construção)\s*[=:]\s*([\d,.]+)\s*m²", "total_built_area"),
        # Área de projeção
        (r"(?:Área de projeção|Projeção)\s*[=:]\s*([\d,.]+)\s*m²", "building_footprint"),
        # Taxa de ocupação
        (r"(?:Taxa de [oO]cupação|TO)\s*[=:]\s*([\d,.]+)\s*%", "taxa_ocupacao"),
        # Recuo frontal
        (r"(?:Recuo [fF]rontal|Afastamento frontal)\s*[=:]\s*([\d,.]+)\s*m", "front_setback"),
        # Recuo fundo
        (r"(?:Recuo de [fF]undos?|Afastamento de fundos?)\s*[=:]\s*([\d,.]+)\s*m", "back_setback"),
        # Altura máxima
        (r"(?:Altura (?:máxima|total)(?: da edificação)?)\s*[=:]\s*([\d,.]+)\s*m", "max_height"),
        # Dimensões do lote (e.g. "25,00 x 10,00" or "25.00m x 10.00m")
        (r"([\d,.]+)\s*[xX×]\s*([\d,.]+)\s*m", "lot_dimensions"),
        # TOTAL de área permeável (alternative format)
        (r"TOTAL\s*\n\s*([\d,.]+)\s*$", "permeable_area_alt"),
    ]

    for pattern, key in patterns:
        matches = re.findall(pattern, text, re.IGNORECASE | re.MULTILINE)
        if matches and key not in found:
            if key == "lot_dimensions":
                w, d = matches[0]
                w = float(w.replace(",", "."))
                d = float(d.replace(",", "."))
                found["lot_area"] = w * d
            elif key == "permeable_area_alt":
                val = float(matches[-1].replace(",", "."))
                if "permeable_area" not in found:
                    found["permeable_area"] = val
            else:
                val = float(matches[0].replace(",", "."))
                found[key] = val

    # Clean up internal keys
    found.pop("permeable_area_alt", None)
    found.pop("lot_dimensions", None)
    found.pop("taxa_ocupacao", None)

    return found


# Keep the original pdf_extractor import working
from cli_civileng.extractors.pdf_extractor import extract_text
