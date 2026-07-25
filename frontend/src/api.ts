import type { Application, ApplicationInput, Stats } from "./types";

const API_BASE = import.meta.env.VITE_API_BASE || "http://localhost:8010";

async function request<T>(path: string, options: RequestInit = {}): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, {
    headers: { "Content-Type": "application/json" },
    ...options,
  });
  if (!res.ok) {
    const body = await res.json().catch(() => ({}));
    throw new Error(body.detail || `Erreur ${res.status}`);
  }
  if (res.status === 204) return undefined as T;
  return res.json();
}

export const api = {
  listApplications: (status?: string) =>
    request<Application[]>(`/api/applications${status ? `?status=${status}` : ""}`),
  createApplication: (data: ApplicationInput) =>
    request<Application>(`/api/applications`, { method: "POST", body: JSON.stringify(data) }),
  updateApplication: (id: number, data: Partial<ApplicationInput>) =>
    request<Application>(`/api/applications/${id}`, { method: "PUT", body: JSON.stringify(data) }),
  deleteApplication: (id: number) =>
    request<void>(`/api/applications/${id}`, { method: "DELETE" }),
  matchApplication: (id: number, jobDescription?: string) =>
    request<Application>(`/api/applications/${id}/match`, {
      method: "POST",
      body: JSON.stringify({ job_description: jobDescription }),
    }),
  getStats: () => request<Stats>(`/api/stats`),
  getProfile: () => request<{ cv_text: string | null }>(`/api/profile`),
  updateProfile: (cvText: string) =>
    request<{ cv_text: string | null }>(`/api/profile`, {
      method: "PUT",
      body: JSON.stringify({ cv_text: cvText }),
    }),
  aiHealth: () => request<{ status: string }>(`/api/ai/health`),
};
