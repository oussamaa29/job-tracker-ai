import json
import logging

import requests
from pydantic import ValidationError

from config import settings
from schemas import MatchResult

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


class AIResponseError(RuntimeError):
    """Le modèle a répondu, mais pas avec un résultat exploitable."""


# Schéma JSON transmis à Ollama (« structured outputs ») : la génération est contrainte
# à ce format, au lieu d'espérer que le modèle respecte les consignes du prompt.
RESPONSE_SCHEMA = MatchResult.model_json_schema()
MAX_ATTEMPTS = 2


def _strip_code_fence(text: str) -> str:
    text = text.strip()
    if text.startswith("```"):
        text = text.removeprefix("```json").removeprefix("```").removesuffix("```").strip()
    return text


def parse_match_result(content: str) -> MatchResult:
    """Valide la réponse du modèle. Lève AIResponseError si elle est inexploitable :
    un score de 0 inventé serait enregistré comme un vrai résultat."""
    try:
        return MatchResult.model_validate_json(_strip_code_fence(content))
    except ValidationError as e:
        raise AIResponseError(f"Réponse IA invalide : {e.error_count()} erreur(s) de format") from e


def _call_ollama(cv_text: str, job_description: str, seed: int) -> str:
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
        "format": RESPONSE_SCHEMA,
        "options": {
            "temperature": 0,
            "seed": seed,
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
    except requests.exceptions.ConnectionError:
        raise ConnectionError("Ollama n'est pas accessible. Démarre-le avec `ollama serve`.")
    except requests.exceptions.Timeout:
        raise TimeoutError("Ollama a mis trop de temps à répondre.")
    except requests.exceptions.HTTPError as e:
        raise AIResponseError(f"Ollama a renvoyé une erreur HTTP {e.response.status_code}") from e
    return resp.json().get("message", {}).get("content", "")


def compute_match(cv_text: str, job_description: str) -> MatchResult:
    """Compare un CV à une offre. Réessaie une fois avec une autre graine si la réponse
    est invalide (avec temperature 0 et la même graine, le modèle répondrait pareil)."""
    last_error: AIResponseError | None = None
    for attempt in range(MAX_ATTEMPTS):
        content = _call_ollama(cv_text, job_description, seed=42 + attempt)
        try:
            return parse_match_result(content)
        except AIResponseError as e:
            logger.warning("Tentative %d : %s", attempt + 1, e)
            last_error = e
    raise last_error
