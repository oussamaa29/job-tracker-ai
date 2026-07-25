import { useEffect, useState, useCallback } from "react";
import "./App.css";
import type { Application, ApplicationInput, Stats, Status } from "./types";
import { STATUS_LABELS, STATUS_ORDER } from "./types";
import { api } from "./api";
import ApplicationCard from "./components/ApplicationCard";
import ApplicationForm from "./components/ApplicationForm";
import MatchingPanel from "./components/MatchingPanel";
import ProfileModal from "./components/ProfileModal";

function App() {
  const [applications, setApplications] = useState<Application[]>([]);
  const [stats, setStats] = useState<Stats | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const [editing, setEditing] = useState<Application | "new" | null>(null);
  const [matching, setMatching] = useState<Application | null>(null);
  const [profileOpen, setProfileOpen] = useState(false);
  const [cvText, setCvText] = useState<string>("");

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const [apps, statsData, profile] = await Promise.all([
        api.listApplications(),
        api.getStats(),
        api.getProfile(),
      ]);
      setApplications(apps);
      setStats(statsData);
      setCvText(profile.cv_text ?? "");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Impossible de charger les données — le backend est-il démarré ?");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    load();
  }, [load]);

  async function handleSave(data: ApplicationInput) {
    if (editing && editing !== "new") {
      const updated = await api.updateApplication(editing.id, data);
      setApplications((apps) => apps.map((a) => (a.id === updated.id ? updated : a)));
    } else {
      const created = await api.createApplication(data);
      setApplications((apps) => [created, ...apps]);
    }
    setEditing(null);
    api.getStats().then(setStats);
  }

  async function handleDelete() {
    if (!editing || editing === "new") return;
    await api.deleteApplication(editing.id);
    setApplications((apps) => apps.filter((a) => a.id !== editing.id));
    setEditing(null);
    api.getStats().then(setStats);
  }

  async function handleProfileSave(text: string) {
    await api.updateProfile(text);
    setCvText(text);
  }

  function handleMatchUpdated(updated: Application) {
    setApplications((apps) => apps.map((a) => (a.id === updated.id ? updated : a)));
    setMatching(updated);
  }

  const byStatus: Record<Status, Application[]> = STATUS_ORDER.reduce((acc, s) => {
    acc[s] = applications.filter((a) => a.status === s);
    return acc;
  }, {} as Record<Status, Application[]>);

  return (
    <div className="app">
      <header className="topbar">
        <div className="brand">
          <h1>Suivi de candidatures</h1>
          <span>Job Tracker + matching IA</span>
        </div>
        <div className="topbar-actions">
          <button className="btn" onClick={() => setProfileOpen(true)}>
            Mon profil {cvText ? "✓" : ""}
          </button>
          <button className="btn primary" onClick={() => setEditing("new")}>
            + Nouvelle candidature
          </button>
        </div>
      </header>

      {stats && (
        <div className="statsbar">
          <span className="statchip">Total <b>{stats.total}</b></span>
          {STATUS_ORDER.map((s) => (
            <span key={s} className="statchip">
              {STATUS_LABELS[s]} <b>{stats.by_status[s] ?? 0}</b>
            </span>
          ))}
        </div>
      )}

      {error && <div className="error-banner">{error}</div>}

      {loading ? (
        <div className="empty-state">Chargement…</div>
      ) : applications.length === 0 && !error ? (
        <div className="empty-state">
          <p>Aucune candidature pour l'instant.</p>
          <button className="btn primary" onClick={() => setEditing("new")}>Ajouter ta première candidature</button>
        </div>
      ) : (
        <div className="board">
          {STATUS_ORDER.map((status) => (
            <div className="column" key={status}>
              <div className="column-head">
                <span>{STATUS_LABELS[status]}</span>
                <span className="column-count">{byStatus[status].length}</span>
              </div>
              <div className="column-cards">
                {byStatus[status].length === 0 && <div className="empty-col">—</div>}
                {byStatus[status].map((app) => (
                  <ApplicationCard
                    key={app.id}
                    app={app}
                    onOpen={() => setEditing(app)}
                    onMatch={() => setMatching(app)}
                  />
                ))}
              </div>
            </div>
          ))}
        </div>
      )}

      {editing && (
        <ApplicationForm
          initial={editing === "new" ? undefined : editing}
          onSave={handleSave}
          onClose={() => setEditing(null)}
          onDelete={editing !== "new" ? handleDelete : undefined}
        />
      )}

      {matching && (
        <MatchingPanel
          application={matching}
          hasProfile={!!cvText}
          onClose={() => setMatching(null)}
          onUpdated={handleMatchUpdated}
        />
      )}

      {profileOpen && (
        <ProfileModal
          initialCv={cvText}
          onClose={() => setProfileOpen(false)}
          onSaved={handleProfileSave}
        />
      )}
    </div>
  );
}

export default App;
