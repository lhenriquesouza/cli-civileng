"""LLM client for rule extraction from PDF text."""
import json
import logging
from openai import OpenAI
from cli_civileng.config import load_config

logger = logging.getLogger(__name__)

MAX_INPUT_CHARS = 12000
MAX_OUTPUT_TOKENS = 4000
DEFAULT_TEMPERATURE = 0.1


def get_client(config_path: str | None = None) -> tuple[OpenAI, str]:
    """Create an OpenAI-compatible client from config.yaml.

    Returns (client, model_name) tuple.
    """
    config = load_config(config_path)
    llm_config = config["llm"]

    if llm_config["provider"] == "openrouter":
        base_url = "https://openrouter.ai/api/v1"
    elif llm_config["provider"] == "deepseek":
        base_url = "https://api.deepseek.com/v1"
    else:
        base_url = llm_config.get("base_url", "https://api.openrouter.ai/api/v1")

    return (
        OpenAI(base_url=base_url, api_key=llm_config["api_key"]),
        llm_config["model"],
    )


EXTRACT_RULES_PROMPT = """You are a civil engineering compliance expert.

Given the text of a construction rules document (condominium or municipal), extract ALL numeric, verifiable rules into a structured JSON format.

The JSON must follow this EXACT schema:
{
  "name": "Name of the condominium or municipality",
  "type": "condominium or municipality",
  "source": "source document name",
  "rules": [
    {
      "id": "R01",
      "name": "Short rule name in Portuguese",
      "description": "Full description in Portuguese",
      "check": "variable_name operator value",
      "unit": "% or m or m²",
      "category": "permeable_area | occupancy | setbacks | height | auxiliary",
      "source_ref": "section/item reference from the document"
    }
  ]
}

RULES FOR THE check FIELD:
- Use these variable names:
  - area_permeavel_pct — permeable area as % of lot
  - taxa_ocupacao_pct — occupation rate as % of lot
  - area_total_construida — total built area in m²
  - recuo_frontal — front setback in m
  - recuo_fundo — back setback in m
  - recuo_lateral — side setback in m
  - altura_maxima — max building height in m
  - altura_terreno_pnt — ground floor height above PNT in m
  - area_edicula_pct — edícula area as % of main building
  - distancia_edicula — distance edícula to main in m
  - afastamento_glp — GLP distance from openings in m
  - altura_muro — wall height in m
  - mezanino_pct — mezzanine area as % of floor below
  - subsolo_pnt — subsoil height above PNT in m
  - recuo_piscina_frente — pool front setback in m
  - recuo_piscina_lateral — pool side/back setback in m

- Operators: >=, <=, >, <, ==
- Values: numbers only, use dot as decimal separator

IMPORTANT: Extract every numeric rule you find. Do not skip any.
Return ONLY the JSON object, no other text."""


def _extract_json_from_response(content: str) -> str:
    """Extract JSON payload from LLM response, handling markdown code fences."""
    if "```json" in content:
        parts = content.split("```json", 1)[1].split("```", 1)
        return parts[0].strip()
    if "```" in content:
        parts = content.split("```", 1)[1].split("```", 1)
        return parts[0].strip()
    return content.strip()


def extract_rules_from_text(text: str, config_path: str | None = None) -> dict:
    """Send PDF text to LLM and get structured rules JSON back.

    Args:
        text: The extracted PDF text content.
        config_path: Optional path to config.yaml.

    Returns:
        Parsed rules dictionary.

    Raises:
        ValueError: If the LLM response cannot be parsed as valid JSON.
    """
    client, model = get_client(config_path)

    response = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": EXTRACT_RULES_PROMPT},
            {
                "role": "user",
                "content": f"Extract all verifiable rules from this document:\n\n{text[:MAX_INPUT_CHARS]}",
            },
        ],
        temperature=DEFAULT_TEMPERATURE,
        max_tokens=MAX_OUTPUT_TOKENS,
    )

    raw_content = response.choices[0].message.content
    json_text = _extract_json_from_response(raw_content)

    try:
        return json.loads(json_text)
    except json.JSONDecodeError as e:
        logger.error("Failed to parse LLM JSON response: %s", e)
        logger.debug("Raw response (first 500 chars): %s", raw_content[:500])
        raise ValueError(
            f"LLM returned invalid JSON. Error: {e}. "
            "Try running again or check the PDF text quality."
        ) from e
