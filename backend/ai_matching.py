import json
import logging

import requests

from config import settings

logger = logging.getLogger("ai_matching")

SYSTEM_PROMPT = """Tu es un assistant de recrutement expert en analyse d'adéquation CV / offre d'emploi.

RÈGLES ABSOLUES :
1. Ne JAMAIS inventer de compétences ou d'expériences qui ne figurent pas dans le CV fourni.
2. Si le CV ou l'offre sont vides ou insuffisants, renvoie un score bas et explique pourquoi dans "reasoning".
3. Réponds UNIQUEMENT en JSON strict, sans texte avant/après, sans balises Markdown.
4. "match_score" est un nombre entre 0 et 100.
5. "keywords_matched" : compétences/mots-clés de l'offre réellement présents dans le CV.
6. "keywords_missing" : compétences/mots-clés importants de l'offre absents du CV.
7. "suggestions" : 2 à 4 actions concrètes pour améliorer l'adéquation (reformulation, compétence à mettre en avant, projet à mentionner).
8. "reasoning" : 2-3 phrases justifiant le score.

FORMAT DE SORTIE STRICT :
{
  "match_score": 72.5,
  "keywords_matched": ["..."],
  "keywords_missing": ["..."],
  "suggestions": ["..."],
  "reasoning": "..."
}
"""


def _extract_json(text: str) -> dict:
    text = text.strip()
    if text.startswith("```"):
        text = text.replace("```json", "").replace("```", "").strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        start, end = text.find("{"), text.rfind("}") + 1
        if start != -1 and end > start:
            try:
                return json.loads(text[start:end])
            except json.JSONDecodeError:
                pass
        return {
            "match_score": 0,
            "keywords_matched": [],
            "keywords_missing": [],
            "suggestions": [],
            "reasoning": "Réponse IA illisible — nouvelle tentative recommandée.",
        }


def compute_match(cv_text: str, job_description: str) -> dict:
    prompt = f"""CV DU CANDIDAT :
{cv_text}

OFFRE D'EMPLOI :
{job_description}

Analyse l'adéquation entre ce CV et cette offre selon les règles données."""

    payload = {
        "model": settings.OLLAMA_MODEL,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": prompt},
        ],
        "stream": False,
        "options": {
            "temperature": 0,
            "seed": 42,
            "top_p": 1.0,
            "top_k": 1,
            "num_ctx": 4096,
        },
    }

    try:
        resp = requests.post(
            f"{settings.OLLAMA_URL}/api/chat", json=payload, timeout=settings.OLLAMA_TIMEOUT
        )
        resp.raise_for_status()
        content = resp.json().get("message", {}).get("content", "")
    except requests.exceptions.ConnectionError:
        raise ConnectionError("Ollama n'est pas accessible. Démarre-le avec `ollama serve`.")
    except requests.exceptions.Timeout:
        raise TimeoutError("Ollama a mis trop de temps à répondre.")

    result = _extract_json(content)
    result.setdefault("match_score", 0)
    result.setdefault("keywords_matched", [])
    result.setdefault("keywords_missing", [])
    result.setdefault("suggestions", [])
    result.setdefault("reasoning", "")
    return result
