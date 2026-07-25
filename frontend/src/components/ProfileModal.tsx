import { useState } from "react";

interface Props {
  initialCv: string;
  onClose: () => void;
  onSaved: (cvText: string) => Promise<void>;
}

export default function ProfileModal({ initialCv, onClose, onSaved }: Props) {
  const [cv, setCv] = useState(initialCv);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    setSaving(true);
    setError(null);
    try {
      await onSaved(cv);
      onClose();
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
        <h2>Mon profil (CV)</h2>
        {error && <div className="error-banner">{error}</div>}
        <form onSubmit={submit}>
          <div className="field">
            <label>Colle le texte de ton CV — il sera réutilisé pour chaque matching IA</label>
            <textarea rows={14} value={cv} onChange={(e) => setCv(e.target.value)} />
          </div>
          <div className="modal-actions">
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
