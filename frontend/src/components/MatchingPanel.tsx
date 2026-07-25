import { useState } from "react";
import type { Application } from "../types";
import { api } from "../api";

interface Props {
  application: Application;
  hasProfile: boolean;
  onClose: () => void;
  onUpdated: (app: Application) => void;
}

function scoreTier(score: number): "high" | "mid" | "low" {
  if (score >= 75) return "high";
  if (score >= 50) return "mid";
  return "low";
}

function parseList(raw?: string | null): string[] {
  if (!raw) return [];
  try {
    const parsed = JSON.parse(raw);
    return Array.isArray(parsed) ? parsed : [];
  } catch {
    return [];
  }
}

export default function MatchingPanel({ application, hasProfile, onClose, onUpdated }: Props) {
  const [jobDescription, setJobDescription] = useState(application.job_description ?? "");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const matched = parseList(application.match_keywords_matched);
  const missing = parseList(application.match_keywords_missing);
  const suggestions = parseList(application.match_suggestions);

  async function runMatch() {
    if (!jobDescription.trim()) {
      setError("Colle la description du poste avant de lancer le matching");
      return;
    }
    if (!hasProfile) {
      setError("Renseigne d'abord ton profil (CV) via le bouton « Mon profil »");
      return;
    }
    setLoading(true);
    setError(null);
    try {
      const updated = await api.matchApplication(application.id, jobDescription);
      onUpdated(updated);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Erreur inconnue");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="overlay" onMouseDown={(e) => e.target === e.currentTarget && onClose()}>
      <div className="modal">
        <button className="modal-close" onClick={onClose} aria-label="Fermer">×</button>
        <h2>Matching IA — {application.company}</h2>
        {error && <div className="error-banner">{error}</div>}

        <div className="field">
          <label>Description du poste</label>
          <textarea
            rows={6}
            value={jobDescription}
            onChange={(e) => setJobDescription(e.target.value)}
            placeholder="Colle ici le texte de l'annonce…"
          />
        </div>
        <div className="modal-actions" style={{ marginTop: 0, marginBottom: 20 }}>
          <button className="btn primary" onClick={runMatch} disabled={loading}>
            {loading ? "Analyse en cours…" : "Lancer le matching"}
          </button>
        </div>

        {application.match_score != null && (
          <>
            <div className="match-score-ring">
              <div className={`ring ${scoreTier(application.match_score)}`}>
                {Math.round(application.match_score)}%
              </div>
              <div className="loading-inline">Score d'adéquation CV / offre</div>
            </div>

            {matched.length > 0 && (
              <div className="kw-group">
                <h4>Compétences en correspondance</h4>
                <div className="kw-list">
                  {matched.map((k) => <span key={k} className="kw matched">{k}</span>)}
                </div>
              </div>
            )}
            {missing.length > 0 && (
              <div className="kw-group">
                <h4>Compétences manquantes</h4>
                <div className="kw-list">
                  {missing.map((k) => <span key={k} className="kw missing">{k}</span>)}
                </div>
              </div>
            )}
            {suggestions.length > 0 && (
              <div className="kw-group">
                <h4>Suggestions</h4>
                <ul className="suggestions">
                  {suggestions.map((s, i) => <li key={i}>{s}</li>)}
                </ul>
              </div>
            )}
            {application.match_reasoning && (
              <div className="reasoning">{application.match_reasoning}</div>
            )}
          </>
        )}
      </div>
    </div>
  );
}
