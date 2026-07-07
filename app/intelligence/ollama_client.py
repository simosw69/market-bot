import ollama
import json
import logging
import os
import re
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

class OllamaClient:
    def __init__(self, host: Optional[str] = None):
        # Use OLLAMA_HOST from environment or default to localhost
        host = host or os.getenv("OLLAMA_HOST", "http://localhost:11434")
        self.client = ollama.Client(host=host)
        self.model = os.getenv("OLLAMA_MODEL", "phi3")  # default to phi3

    def analyze_listing(self, titolo: str, descrizione: str = "") -> Dict[str, Any]:
        """
        Analyze a listing title and description to determine if it's a good deal.
        Returns a dictionary with keys: affidabilita (0-10), motivo, categoria, prezzo_giusto (bool), etc.
        """
        prompt = f"""Analizza questo titolo e descrizione:
Titolo: '{titolo}'
Descrizione: '{descrizione}'

Pensi che l'oggetto sia venduto al prezzo corretto? Rispondi in formato JSON:
{{
    'affidabilita': 0-10,
    'motivo': 'spiegazione breve',
    'categoria': 'categoria stimata',
    'prezzo_giusto': true/false,
    'suggerimento_prezzo': 0.0  // suggested fair price if known
}}
"""
        try:
            response = self.client.generate(model=self.model, prompt=prompt)
            # Extract JSON from response
            resp_text = response['response']
            # Find JSON object in the response
            json_match = re.search(r'\{.*\}', resp_text, re.DOTALL)
            if json_match:
                json_str = json_match.group()
                # Convert single quotes to double quotes for valid JSON
                json_str = json_str.replace("'", '"')
                # Sometimes the JSON might have trailing commas, we can try to load and if fails, try to fix
                try:
                    result = json.loads(json_str)
                except json.JSONDecodeError:
                    # Try to fix common issues
                    json_str = re.sub(r',\s*}', '}', json_str)  # remove trailing commas before }
                    json_str = re.sub(r',\s*]', ']', json_str)  # remove trailing commas before ]
                    result = json.loads(json_str)
                return result
            else:
                logger.error(f"Could not extract JSON from Ollama response: {resp_text}")
                return {}
        except Exception as e:
            logger.error(f"Error calling Ollama: {e}")
            return {}

    def categorize_title(self, titolo: str) -> str:
        """Use Ollama to predict category from title."""
        prompt = f"Qual è la categoria più probabile per questo oggetto: '{titolo}'? Rispondi solo con il nome della categoria."
        try:
            response = self.client.generate(model=self.model, prompt=prompt)
            return response['response'].strip()
        except Exception as e:
            logger.error(f"Error categorizing title: {e}")
            return ""