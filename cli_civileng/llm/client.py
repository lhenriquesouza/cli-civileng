"""LLM client for rule extraction from PDF text."""
import json
from openai import OpenAI
from cli_civileng.config import load_config


def get_client(config_path=None):
    """Create an OpenAI-compatible client from config.yaml."""
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


def extract_rules_from_text(text: str, config_path=None) -> dict:
    """Send PDF text to LLM and get structured rules JSON back."""
    client, model = get_client(config_path)

    response = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": EXTRACT_RULES_PROMPT},
            {
                "role": "user",
                "content": f"Extract all verifiable rules from this document:\n\n{text[:12000]}",
            },
        ],
        temperature=0.1,
        max_tokens=4000,
    )

    content = response.choices[0].message.content
    # Extract JSON from response (may be wrapped in ```json)
    if "```json" in content:
        content = content.split("```json")[1].split("```")[0]
    elif "```" in content:
        content = content.split("```")[1].split("```")[0]

    return json.loads(content)
