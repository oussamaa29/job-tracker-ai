import json

import pytest

import main
from ai_matching import AIResponseError
from schemas import MatchResult

APPLICATION = {"company": "Acme", "position": "Développeur fullstack", "status": "applied"}
RESULT = MatchResult(
    match_score=80,
    keywords_matched=["React"],
    keywords_missing=["Go"],
    suggestions=["Ajouter un projet Go"],
    reasoning="Profil proche.",
)


def create(client, **overrides):
    resp = client.post("/api/applications", json={**APPLICATION, **overrides})
    assert resp.status_code == 201
    return resp.json()


def test_crud(client):
    app = create(client)
    assert client.get(f"/api/applications/{app['id']}").json()["company"] == "Acme"

    updated = client.put(f"/api/applications/{app['id']}", json={"status": "interview"}).json()
    assert updated["status"] == "interview"
    assert updated["position"] == "Développeur fullstack"  # champs non envoyés conservés

    assert client.delete(f"/api/applications/{app['id']}").status_code == 204
    assert client.get(f"/api/applications/{app['id']}").status_code == 404


def test_unknown_status_is_rejected(client):
    assert client.post("/api/applications", json={**APPLICATION, "status": "ghosted"}).status_code == 422
    app = create(client)
    assert client.put(f"/api/applications/{app['id']}", json={"status": "ghosted"}).status_code == 422
    assert client.get("/api/applications?status=ghosted").status_code == 422


def test_filter_and_stats(client):
    create(client)
    create(client, status="offer")
    create(client, status="offer")
    assert len(client.get("/api/applications?status=offer").json()) == 2
    assert client.get("/api/stats").json() == {"total": 3, "by_status": {"applied": 1, "offer": 2}}


def test_profile_is_created_then_updated(client):
    assert client.get("/api/profile").json() == {"cv_text": None}
    client.put("/api/profile", json={"cv_text": "CV v1"})
    client.put("/api/profile", json={"cv_text": "CV v2"})
    assert client.get("/api/profile").json() == {"cv_text": "CV v2"}


@pytest.fixture
def with_cv(client):
    client.put("/api/profile", json={"cv_text": "Mon CV"})


def test_match_requires_a_job_description(client, with_cv):
    app = create(client)
    resp = client.post(f"/api/applications/{app['id']}/match", json={})
    assert resp.status_code == 400


def test_match_requires_a_cv(client):
    app = create(client, job_description="Offre")
    assert client.post(f"/api/applications/{app['id']}/match", json={}).status_code == 400


def test_match_is_stored(client, with_cv, monkeypatch):
    seen = {}

    def fake(cv, offer):
        seen.update(cv=cv, offer=offer)
        return RESULT

    monkeypatch.setattr(main, "compute_match", fake)
    app = create(client)
    body = client.post(f"/api/applications/{app['id']}/match", json={"job_description": "Offre"}).json()
    assert seen == {"cv": "Mon CV", "offer": "Offre"}
    assert body["match_score"] == 80
    assert json.loads(body["match_keywords_missing"]) == ["Go"]
    assert body["job_description"] == "Offre"


def test_invalid_ai_answer_returns_502_and_keeps_previous_result(client, with_cv, monkeypatch):
    app = create(client, job_description="Offre")
    monkeypatch.setattr(main, "compute_match", lambda cv, offer: RESULT)
    client.post(f"/api/applications/{app['id']}/match", json={})

    def broken(cv, offer):
        raise AIResponseError("Réponse IA invalide : 1 erreur(s) de format")

    monkeypatch.setattr(main, "compute_match", broken)
    resp = client.post(f"/api/applications/{app['id']}/match", json={})
    assert resp.status_code == 502
    assert "Relance" in resp.json()["detail"]
    assert client.get(f"/api/applications/{app['id']}").json()["match_score"] == 80


def test_ollama_down_returns_503(client, with_cv, monkeypatch):
    def down(cv, offer):
        raise ConnectionError("Ollama n'est pas accessible.")

    monkeypatch.setattr(main, "compute_match", down)
    app = create(client, job_description="Offre")
    assert client.post(f"/api/applications/{app['id']}/match", json={}).status_code == 503


def test_match_on_unknown_application(client):
    assert client.post("/api/applications/999/match", json={}).status_code == 404
