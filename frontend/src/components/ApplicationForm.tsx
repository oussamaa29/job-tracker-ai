import { useState } from "react";
import type { Application, ApplicationInput, Status } from "../types";
import { STATUS_LABELS, STATUS_ORDER } from "../types";

interface Props {
  initial?: Application;
  onSave: (data: ApplicationInput) => Promise<void>;
  onClose: () => void;
  onDelete?: () => void;
}

export default function ApplicationForm({ initial, onSave, onClose, onDelete }: Props) {
  const [form, setForm] = useState<ApplicationInput>({
    company: initial?.company ?? "",
    position: initial?.position ?? "",
    status: initial?.status ?? "to_apply",
    job_url: initial?.job_url ?? "",
    location: initial?.location ?? "",
    salary_range: initial?.salary_range ?? "",
    source: initial?.source ?? "",
    applied_date: initial?.applied_date ?? "",
    notes: initial?.notes ?? "",
    job_description: initial?.job_description ?? "",
  });
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  function set<K extends keyof ApplicationInput>(key: K, value: ApplicationInput[K]) {
    setForm((f) => ({ ...f, [key]: value }));
  }

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    if (!form.company.trim() || !form.position.trim()) {
      setError("L'entreprise et le poste sont obligatoires");
      return;
    }
    setSaving(true);
    setError(null);
    try {
      await onSave(form);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Erreur inconnue");
    } finally {
      setSaving(false);
    }
  }

  return (
    <div className="overlay" onMouseDown={(e) => e.target === e.currentTarget && onClose()}>
      <div className="modal">
        <button className="modal-close" onClick={onClose} aria-label="Fermer">×</button>
        <h2>{initial ? "Modifier la candidature" : "Nouvelle candidature"}</h2>
        {error && <div className="error-banner">{error}</div>}
        <form onSubmit={submit}>
          <div className="field-row">
            <div className="field">
              <label>Entreprise *</label>
              <input value={form.company} onChange={(e) => set("company", e.target.value)} required />
            </div>
            <div className="field">
              <label>Poste *</label>
              <input value={form.position} onChange={(e) => set("position", e.target.value)} required />
            </div>
          </div>
          <div className="field-row">
            <div className="field">
              <label>Statut</label>
              <select value={form.status} onChange={(e) => set("status", e.target.value as Status)}>
                {STATUS_ORDER.map((s) => (
                  <option key={s} value={s}>{STATUS_LABELS[s]}</option>
                ))}
              </select>
            </div>
            <div className="field">
              <label>Source</label>
              <input value={form.source ?? ""} onChange={(e) => set("source", e.target.value)} placeholder="LinkedIn, référence…" />
            </div>
          </div>
          <div className="field-row">
            <div className="field">
              <label>Lieu</label>
              <input value={form.location ?? ""} onChange={(e) => set("location", e.target.value)} />
            </div>
            <div className="field">
              <label>Fourchette de salaire</label>
              <input value={form.salary_range ?? ""} onChange={(e) => set("salary_range", e.target.value)} />
            </div>
          </div>
          <div className="field">
            <label>Lien de l'offre</label>
            <input value={form.job_url ?? ""} onChange={(e) => set("job_url", e.target.value)} placeholder="https://…" />
          </div>
          <div className="field">
            <label>Date de candidature</label>
            <input type="date" value={form.applied_date ?? ""} onChange={(e) => set("applied_date", e.target.value)} />
          </div>
          <div className="field">
            <label>Description du poste (pour le matching IA)</label>
            <textarea value={form.job_description ?? ""} onChange={(e) => set("job_description", e.target.value)} />
          </div>
          <div className="field">
            <label>Notes</label>
            <textarea value={form.notes ?? ""} onChange={(e) => set("notes", e.target.value)} />
          </div>
          <div className="modal-actions">
            {initial && onDelete && (
              <button type="button" className="btn danger" onClick={onDelete}>Supprimer</button>
            )}
            <button type="button" className="btn ghost" onClick={onClose}>Annuler</button>
            <button type="submit" className="btn primary" disabled={saving}>
              {saving ? "Enregistrement…" : "Enregistrer"}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
