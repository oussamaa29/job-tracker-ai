# Job Tracker IA

Suivi de candidatures avec matching IA entre ton CV et une offre d'emploi. Kanban par statut, profil CV réutilisable, score d'adéquation généré par un LLM local (Ollama) avec mots-clés en correspondance/manquants et suggestions concrètes.

## Pourquoi ce projet

Centraliser ses candidatures (statuts, relances, deadlines) et comparer automatiquement une offre à son propre CV pour savoir où postuler en priorité et quoi ajuster dans son profil.

## Stack

| Couche | Techno |
|--------|--------|
| Frontend | React + TypeScript (Vite) |
| Backend | FastAPI (Python) |
| Base de données | SQLite (via SQLAlchemy) |
| IA | Ollama local — modèle `mistral:latest`, appels déterministes (temperature 0, seed fixe) |

## Lancer le projet en local

### Backend

```bash
cd backend
python -m venv venv
venv/Scripts/activate        # Windows
pip install -r requirements.txt
cp .env.example .env
uvicorn main:app --reload --port 8010
```

### Frontend

```bash
cd frontend
npm install
cp .env.example .env
npm run dev
```

Ouvrir `http://localhost:5173`. Le matching IA nécessite Ollama démarré (`ollama serve`) avec le modèle `mistral:latest` (`ollama pull mistral`).

## Fonctionnalités

- CRUD complet des candidatures (entreprise, poste, statut, source, lieu, salaire, notes, description de poste)
- Vue Kanban par statut (À postuler → Postulé → Pré-qualification → Entretien → Offre reçue / Refusé / Retiré)
- Profil CV unique réutilisé pour chaque matching
- Matching IA : score d'adéquation, compétences en correspondance / manquantes, suggestions d'amélioration, justification
- Statistiques en tête de page (total et répartition par statut)

## Structure

```
job-tracker-ai/
├── backend/
│   ├── main.py            # Routes FastAPI (CRUD, matching, profil, stats)
│   ├── models.py           # Modèles SQLAlchemy
│   ├── schemas.py          # Schémas Pydantic
│   ├── ai_matching.py       # Appel Ollama + parsing JSON
│   ├── database.py
│   └── config.py
└── frontend/
    └── src/
        ├── App.tsx          # Board Kanban
        ├── api.ts           # Client HTTP
        ├── types.ts
        └── components/
            ├── ApplicationForm.tsx
            ├── ApplicationCard.tsx
            ├── MatchingPanel.tsx
            └── ProfileModal.tsx
```
