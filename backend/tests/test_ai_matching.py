import json

import pytest
import requests

import ai_matching
from ai_matching import AIResponseError, compute_match, parse_match_result

VALID = {
    "match_score": 72.5,
    "keywords_matched": ["React", "TypeScript"],
    "keywords_missing": ["Kubernetes"],
    "suggestions": ["Mettre en avant le projet Tandem"],
    "reasoning": "Bonne base front, peu d'expérience infra.",
}


class FakeResponse:
    def __init__(self, content, status=200):
        self._content = content
        self.status_code = status

    def raise_for_status(self):
        if self.status_code >= 400:
            raise requests.exceptions.HTTPError(response=self)

    def json(self):
        return {"message": {"content": self._content}}


@pytest.fixture
def ollama(monkeypatch):
    """Simule Ollama : renvoie les réponses données, dans l'ordre, et garde les requêtes."""
    calls = []

    def install(*contents):
        queue = list(contents)

        def post(url, json, timeout):
            calls.append(json)
            item = queue.pop(0)
            if isinstance(item, Exception):
                raise item
            return item if isinstance(item, FakeResponse) else FakeResponse(item)

        monkeypatch.setattr(ai_matching.requests, "post", post)
        return calls

    return install


def test_valid_response_is_parsed(ollama):
    calls = ollama(json.dumps(VALID))
    result = compute_match("CV", "Offre")
    assert result.match_score == 72.5
    assert result.keywords_missing == ["Kubernetes"]
    # La génération est contrainte par le schéma JSON du résultat
    assert calls[0]["format"]["properties"]["match_score"]["maximum"] == 100
    assert calls[0]["options"]["temperature"] == 0


def test_markdown_fence_is_tolerated():
    assert parse_match_result("```json\n" + json.dumps(VALID) + "\n```").match_score == 72.5


@pytest.mark.parametrize(
    "content",
    [
        "Je pense que le score est de 70 %.",            # pas du JSON
        json.dumps({**VALID, "match_score": 140}),        # hors bornes
        json.dumps({**VALID, "match_score": -5}),
        json.dumps({k: v for k, v in VALID.items() if k != "reasoning"}),  # champ manquant
        json.dumps({**VALID, "suggestions": "une seule chaîne"}),          # mauvais type
    ],
)
def test_invalid_responses_are_rejected_instead_of_scored_zero(content):
    with pytest.raises(AIResponseError):
        parse_match_result(content)


def test_invalid_first_answer_is_retried_with_another_seed(ollama):
    calls = ollama("pas du json", json.dumps(VALID))
    assert compute_match("CV", "Offre").match_score == 72.5
    assert [c["options"]["seed"] for c in calls] == [42, 43]


def test_two_invalid_answers_raise(ollama):
    ollama("pas du json", "toujours pas")
    with pytest.raises(AIResponseError):
        compute_match("CV", "Offre")


def test_ollama_unreachable(ollama):
    ollama(requests.exceptions.ConnectionError())
    with pytest.raises(ConnectionError, match="ollama serve"):
        compute_match("CV", "Offre")


def test_ollama_timeout(ollama):
    ollama(requests.exceptions.Timeout())
    with pytest.raises(TimeoutError):
        compute_match("CV", "Offre")


def test_ollama_http_error_is_reported(ollama):
    ollama(FakeResponse("", status=404))  # par exemple : modèle non téléchargé
    with pytest.raises(AIResponseError, match="404"):
        compute_match("CV", "Offre")
