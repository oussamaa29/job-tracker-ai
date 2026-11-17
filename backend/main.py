import json
import logging
from typing import List, Optional

from fastapi import FastAPI, Depends, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from sqlalchemy import func

from config import settings
from database import Base, engine, get_db
import models
import schemas
from ai_matching import AIResponseError, compute_match

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("job-tracker")

Base.metadata.create_all(bind=engine)

app = FastAPI(title="Job Application Tracker API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health():
    return {"status": "healthy"}


@app.get("/api/ai/health")
def ai_health():
    import requests

    try:
        r = requests.get(f"{settings.OLLAMA_URL}/api/tags", timeout=5)
        r.raise_for_status()
        models_available = [m.get("name") for m in r.json().get("models", [])]
        return {"status": "healthy", "models_available": models_available}
    except Exception as e:
        return {"status": "unhealthy", "error": str(e)}


# ---------------- Applications CRUD ----------------

@app.get("/api/applications", response_model=List[schemas.ApplicationOut])
def list_applications(status: Optional[schemas.Status] = Query(None), db: Session = Depends(get_db)):
    q = db.query(models.Application)
    if status:
        q = q.filter(models.Application.status == status)
    return q.order_by(models.Application.updated_at.desc()).all()


@app.post("/api/applications", response_model=schemas.ApplicationOut, status_code=201)
def create_application(payload: schemas.ApplicationCreate, db: Session = Depends(get_db)):
    app_obj = models.Application(**payload.model_dump())
    db.add(app_obj)
    db.commit()
    db.refresh(app_obj)
    return app_obj


@app.get("/api/applications/{app_id}", response_model=schemas.ApplicationOut)
def get_application(app_id: int, db: Session = Depends(get_db)):
    app_obj = db.get(models.Application, app_id)
    if not app_obj:
        raise HTTPException(404, "Candidature introuvable")
    return app_obj


@app.put("/api/applications/{app_id}", response_model=schemas.ApplicationOut)
def update_application(app_id: int, payload: schemas.ApplicationUpdate, db: Session = Depends(get_db)):
    app_obj = db.get(models.Application, app_id)
    if not app_obj:
        raise HTTPException(404, "Candidature introuvable")
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(app_obj, field, value)
    db.commit()
    db.refresh(app_obj)
    return app_obj


@app.delete("/api/applications/{app_id}", status_code=204)
def delete_application(app_id: int, db: Session = Depends(get_db)):
    app_obj = db.get(models.Application, app_id)
    if not app_obj:
        raise HTTPException(404, "Candidature introuvable")
    db.delete(app_obj)
    db.commit()
    return None


# ---------------- AI matching ----------------

@app.post("/api/applications/{app_id}/match", response_model=schemas.ApplicationOut)
def match_application(app_id: int, payload: schemas.MatchRequest, db: Session = Depends(get_db)):
    app_obj = db.get(models.Application, app_id)
    if not app_obj:
        raise HTTPException(404, "Candidature introuvable")

    job_description = payload.job_description or app_obj.job_description
    if not job_description:
        raise HTTPException(400, "Aucune description de poste fournie ou enregistrée pour cette candidature")

    profile = db.query(models.Profile).first()
    cv_text = payload.cv_text or (profile.cv_text if profile else None)
    if not cv_text:
        raise HTTPException(400, "Aucun CV enregistré — renseigne ton profil avant de lancer le matching")

    try:
        result = compute_match(cv_text, job_description)
    except (ConnectionError, TimeoutError) as e:
        raise HTTPException(503, str(e))
    except AIResponseError as e:
        # Rien n'est enregistré : l'ancien résultat (s'il existe) reste affiché
        raise HTTPException(502, f"{e}. Relance le matching.")

    app_obj.job_description = job_description
    app_obj.match_score = result.match_score
    app_obj.match_keywords_matched = json.dumps(result.keywords_matched, ensure_ascii=False)
    app_obj.match_keywords_missing = json.dumps(result.keywords_missing, ensure_ascii=False)
    app_obj.match_suggestions = json.dumps(result.suggestions, ensure_ascii=False)
    app_obj.match_reasoning = result.reasoning
    db.commit()
    db.refresh(app_obj)
    return app_obj


# ---------------- Profile (CV) ----------------

@app.get("/api/profile", response_model=schemas.ProfileOut)
def get_profile(db: Session = Depends(get_db)):
    profile = db.query(models.Profile).first()
    if not profile:
        return schemas.ProfileOut(cv_text=None)
    return profile


@app.put("/api/profile", response_model=schemas.ProfileOut)
def update_profile(payload: schemas.ProfileUpdate, db: Session = Depends(get_db)):
    profile = db.query(models.Profile).first()
    if not profile:
        profile = models.Profile(cv_text=payload.cv_text)
        db.add(profile)
    else:
        profile.cv_text = payload.cv_text
    db.commit()
    db.refresh(profile)
    return profile


# ---------------- Stats ----------------

@app.get("/api/stats", response_model=schemas.StatsOut)
def get_stats(db: Session = Depends(get_db)):
    total = db.query(func.count(models.Application.id)).scalar()
    rows = (
        db.query(models.Application.status, func.count(models.Application.id))
        .group_by(models.Application.status)
        .all()
    )
    by_status = {status: count for status, count in rows}
    return {"total": total, "by_status": by_status}
