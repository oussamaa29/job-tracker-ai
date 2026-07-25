import type { Application } from "../types";

interface Props {
  app: Application;
  onOpen: () => void;
  onMatch: () => void;
}

function scoreTier(score: number): "high" | "mid" | "low" {
  if (score >= 75) return "high";
  if (score >= 50) return "mid";
  return "low";
}

export default function ApplicationCard({ app, onOpen, onMatch }: Props) {
  return (
    <div className="card" onClick={onOpen}>
      <h3>{app.position}</h3>
      <div className="company">{app.company}</div>
      <div className="card-meta">
        <span>{app.location || app.source || "—"}</span>
        {app.match_score != null ? (
          <span className={`score ${scoreTier(app.match_score)}`}>{Math.round(app.match_score)}%</span>
        ) : (
          <button
            type="button"
            className="btn small ghost"
            onClick={(e) => {
              e.stopPropagation();
              onMatch();
            }}
          >
            Matching IA
          </button>
        )}
      </div>
    </div>
  );
}
