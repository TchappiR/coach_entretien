import requests
import os
import json
from dotenv import load_dotenv

load_dotenv()

API_ENDPOINT = "https://api.firecrawl.dev/v1/scrape"
API_KEY = os.environ['FIRECRAWL_API_KEY']
SCHEMA = {
    "type": "object",
    "properties": {
        "titre_poste": {"type": "string"},
        "entreprise": {"type": "string"},
        "description_detaillee": {"type": "string"},
        "competences_techniques": {"type": "array", "items": {"type": "string"}},
        "soft_skills": {"type": "array", "items": {"type": "string"}},
        "niveau_experience": {"type": "string"},
        "salaire": {"type": "string"},
        "lieu": {"type": "string"}
    },
    "required": ["titre_poste", "description_detaillee"]
}


def scrape_job_offer(url: str, schema: dict = SCHEMA, timeout: int = 6000) -> dict:
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json"
    }

    payload = {
        "url": url,
        "formats": ["extract"],
        "extract": {
            "schema": schema
        },
        "waitFor": timeout
    }

    response = requests.post(API_ENDPOINT, headers=headers, json=payload, timeout=10) 

    data = response.json()
    
    info_extraite = data.get('data', {}).get('extract')
    return info_extraite



def save_to_json(data: dict, filename: str):
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=4)
