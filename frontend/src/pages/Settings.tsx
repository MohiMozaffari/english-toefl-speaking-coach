import { useEffect, useState } from "react";
import { api } from "../api";
import { useProfile } from "../contexts";
import { PageHeader } from "../components/ui";
import type { HealthStatus, Settings as SettingsData } from "../types";

const WHISPER_OPTIONS = [
  { value: "tiny", label: "tiny (fastest, least accurate)" },
  { value: "base", label: "base (balanced, safe default on slower CPUs)" },
  { value: "small", label: "small (best accuracy, slower on CPU)" },
];

export default function Settings() {
  const { profile, refreshProfiles } = useProfile();
  const [form, setForm] = useState<SettingsData>({ base_url: "", api_key: "", model: "", whisper_model: "small" });
  const [goal, setGoal] = useState<number>(50);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [saved, setSaved] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [health, setHealth] = useState<HealthStatus | null>(null);

  useEffect(() => {
    api
      .getSettings()
      .then(setForm)
      .catch((err) => setError(err.message))
      .finally(() => setLoading(false));
    refreshHealth();
  }, []);

  useEffect(() => {
    if (profile) setGoal(profile.daily_goal_xp);
  }, [profile]);

  const refreshHealth = () => {
    api.getHealth().then(setHealth).catch(() => setHealth(null));
  };

  const update = (key: keyof SettingsData) => (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>) =>
    setForm((f) => ({ ...f, [key]: e.target.value }));

  const handleSave = async (e: React.FormEvent) => {
    e.preventDefault();
    setSaving(true);
    setSaved(false);
    setError(null);
    try {
      const result = await api.saveSettings(form);
      setForm(result);
      if (profile && goal !== profile.daily_goal_xp) {
        await api.updateProfile(profile.id, { daily_goal_xp: goal });
        await refreshProfiles();
      }
      setSaved(true);
      refreshHealth();
      setTimeout(() => setSaved(false), 2500);
    } catch (err) {
      setError((err as Error).message);
    } finally {
      setSaving(false);
    }
  };

  if (loading) return <p className="muted">Loading settings…</p>;

  return (
    <div>
      <PageHeader title="Settings" subtitle="Everything is stored locally on this machine — the key is never logged anywhere." />

      <div className="card">
        <form onSubmit={handleSave}>
          <label htmlFor="api_key">FreeLLMAPI unified key</label>
          <input
            id="api_key"
            type="password"
            placeholder="freellmapi-xxxxxxxx"
            value={form.api_key}
            onChange={update("api_key")}
            autoComplete="off"
          />

          <label htmlFor="base_url">FreeLLMAPI base URL</label>
          <input id="base_url" type="text" value={form.base_url} onChange={update("base_url")} />

          <label htmlFor="model">Model</label>
          <input id="model" type="text" placeholder="auto" value={form.model} onChange={update("model")} />
          <p className="muted small" style={{ marginTop: 4 }}>
            Leave as "auto" to let FreeLLMAPI's router pick the best available free model, or type an exact model name to pin it.
          </p>

          <label htmlFor="whisper_model">faster-whisper model size</label>
          <select id="whisper_model" value={form.whisper_model} onChange={update("whisper_model")}>
            {WHISPER_OPTIONS.map((opt) => (
              <option key={opt.value} value={opt.value}>{opt.label}</option>
            ))}
          </select>

          {profile && (
            <>
              <label htmlFor="daily_goal">Daily XP goal ({profile.name})</label>
              <input
                id="daily_goal"
                type="number"
                min={10}
                max={500}
                step={10}
                value={goal}
                onChange={(e) => setGoal(Number(e.target.value))}
              />
              <p className="muted small" style={{ marginTop: 4 }}>
                Rough guide: one TOEFL set ≈ 40-70 XP, a shadowing sentence ≈ 3 XP, a listening quiz ≈ 10-18 XP.
              </p>
            </>
          )}

          <div className="row" style={{ marginTop: 20 }}>
            <button type="submit" className="primary" disabled={saving}>
              {saving ? "Saving…" : "Save settings"}
            </button>
            {saved && <span className="badge good pop-in">Saved ✓</span>}
          </div>
        </form>

        {error && <div className="error-box">{error}</div>}
      </div>

      {health && (
        <div className="card">
          <p className="section-title">Connection check</p>
          <div className="grid cols-2">
            <div>
              <div className="flex-between">
                <span>FreeLLMAPI</span>
                <span className={`badge ${health.llm.reachable ? "good" : "bad"}`}>
                  {health.llm.reachable ? "Connected" : "Unreachable"}
                </span>
              </div>
              <p className="muted small">{health.llm.message}</p>
            </div>
            <div>
              <div className="flex-between">
                <span>faster-whisper</span>
                <span className={`badge ${health.whisper.installed ? "good" : "bad"}`}>
                  {health.whisper.installed ? "Installed" : "Missing"}
                </span>
              </div>
              <p className="muted small">{health.whisper.message}</p>
            </div>
          </div>
          <button type="button" onClick={refreshHealth} style={{ marginTop: 10 }}>Re-check</button>
        </div>
      )}
    </div>
  );
}
