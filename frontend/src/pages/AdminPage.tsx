import { useEffect, useState } from "react";
import { Activity, ArrowLeft, CheckCircle2, KeyRound, LogOut, RotateCcw, Save, ServerCog, ShieldCheck, Trash2 } from "lucide-react";
import { Link } from "react-router-dom";

type Profile = { slug: string; label: string; model: string; base_url: string; timeout: number; temperature: number; reasoning_effort: string; json_mode: boolean; prompt: string; qps: number; workers: number; enabled: boolean; version: number };
type Usage = { summary: Record<string, number>; failures: { created_at: string; tier: string; error: string }[] };
type Version = { version: number; created_at: number; current: boolean };

async function request<T>(url: string, options?: RequestInit): Promise<T> {
  const response = await fetch(url, options);
  if (!response.ok) { const body = await response.json().catch(() => ({})); throw new Error(body.detail || "请求失败"); }
  if (response.status === 204) return undefined as T;
  return response.json();
}

function Login({ onSuccess }: { onSuccess: () => void }) {
  const [token, setToken] = useState("");
  const [error, setError] = useState("");
  const submit = async (event: React.FormEvent) => {
    event.preventDefault(); setError("");
    try { await request("/admin/login", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ username: "admin", token }) }); onSuccess(); }
    catch (reason) { setError((reason as Error).message); }
  };
  return <main className="admin-login"><form onSubmit={submit}><span className="admin-mark"><ShieldCheck size={23} /></span><h1>管理后台</h1><p>使用管理密钥登录 BilingualPDF。</p><label>用户名<input value="admin" disabled /></label><label>管理密钥<input type="password" value={token} onChange={(event) => setToken(event.target.value)} autoFocus autoComplete="current-password" /></label>{error && <div className="notice error">{error}</div>}<button className="button primary" disabled={!token}>登录</button><Link to="/"><ArrowLeft size={16} />返回用户端</Link></form></main>;
}

function TierEditor({ initial, isDefault, onSaved, onDefault }: { initial: Profile; isDefault: boolean; onSaved: () => void; onDefault: () => void }) {
  const [profile, setProfile] = useState(initial);
  const [testKey, setTestKey] = useState("");
  const [message, setMessage] = useState("");
  const [versions, setVersions] = useState<Version[]>([]);
  useEffect(() => setProfile(initial), [initial]);
  useEffect(() => { request<Version[]>(`/admin/api/tiers/${initial.slug}/versions`).then(setVersions).catch(() => setVersions([])); }, [initial]);
  const set = (key: keyof Profile, value: string | number | boolean) => setProfile((current) => ({ ...current, [key]: value }));
  const save = async () => { try { await request("/admin/api/tiers", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(profile) }); setMessage("配置已保存，仅影响新任务"); onSaved(); } catch (e) { setMessage((e as Error).message); } };
  const test = async () => { try { await request("/admin/api/test", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ slug: profile.slug, api_key: testKey }) }); setTestKey(""); setMessage("配置测试成功"); } catch (e) { setMessage((e as Error).message); } };
  const rollback = async (version: number) => { try { await request(`/admin/api/tiers/${profile.slug}/rollback/${version}`, { method: "POST" }); setMessage(`已回滚到版本 ${version}`); onSaved(); } catch (e) { setMessage((e as Error).message); } };
  return <section className="admin-section"><div className="section-heading compact"><div><h2>{profile.label}</h2><p>版本 {profile.version} {isDefault ? "· 当前默认" : ""}</p></div><label className="switch"><input type="checkbox" checked={profile.enabled} onChange={(e) => set("enabled", e.target.checked)} /><span />启用</label></div>
    <div className="admin-form-grid"><label>模型 ID<input value={profile.model} onChange={(e) => set("model", e.target.value)} /></label><label>服务地址<input value={profile.base_url} onChange={(e) => set("base_url", e.target.value)} /></label><label>超时（秒）<input type="number" value={profile.timeout} onChange={(e) => set("timeout", +e.target.value)} /></label><label>Temperature<input type="number" step="0.1" value={profile.temperature} onChange={(e) => set("temperature", +e.target.value)} /></label><label>QPS<input type="number" step="0.1" value={profile.qps} onChange={(e) => set("qps", +e.target.value)} /></label><label>工作线程<input type="number" value={profile.workers} onChange={(e) => set("workers", +e.target.value)} /></label></div>
    <label>系统提示词<textarea rows={3} value={profile.prompt} onChange={(e) => set("prompt", e.target.value)} /></label>
    <div className="button-row"><button className="button primary" onClick={save}><Save size={17} />保存新版本</button>{!isDefault && profile.enabled && <button className="button secondary" onClick={onDefault}><CheckCircle2 size={17} />设为默认</button>}</div>
    <div className="test-row"><label>临时测试 Key<input type="password" value={testKey} onChange={(e) => setTestKey(e.target.value)} placeholder="测试后立即丢弃" /></label><button className="button secondary" disabled={!testKey} onClick={test}><KeyRound size={17} />发送最小请求</button></div><small className="cost-note">测试请求可能产生少量费用。</small>{message && <div className="notice">{message}</div>}
    {versions.length > 1 && <div className="version-list"><strong>配置版本</strong>{versions.slice(0, 5).map((item) => <div key={item.version}><span>版本 {item.version}<small>{new Date(item.created_at * 1000).toLocaleString("zh-CN")}</small></span>{item.current ? <em>当前</em> : <button className="text-button" onClick={() => rollback(item.version)}><RotateCcw size={14} />回滚</button>}</div>)}</div>}
  </section>;
}

export function AdminPage() {
  const [authenticated, setAuthenticated] = useState<boolean | null>(null);
  const [profiles, setProfiles] = useState<Profile[]>([]);
  const [defaultTier, setDefaultTier] = useState("standard");
  const [usage, setUsage] = useState<Usage | null>(null);
  const load = async () => {
    try {
      await request("/admin/api/session"); setAuthenticated(true);
      const [tiers, metrics] = await Promise.all([request<{ tiers: Profile[]; default_tier: string }>("/admin/api/tiers"), request<Usage>("/admin/api/usage")]);
      setProfiles(tiers.tiers); setDefaultTier(tiers.default_tier); setUsage(metrics);
    } catch { setAuthenticated(false); }
  };
  useEffect(() => { load(); }, []);
  if (authenticated === null) return <div className="page-loading">正在验证管理会话...</div>;
  if (!authenticated) return <Login onSuccess={load} />;
  const logout = async () => { await request("/admin/logout", { method: "POST" }); setAuthenticated(false); };
  const cleanup = async () => { const result = await request<{ files: number; jobs: number }>("/admin/api/cleanup", { method: "POST" }); alert(`已清理 ${result.files} 个文件目录、${result.jobs} 条历史记录`); load(); };
  return <div className="admin-shell"><header className="admin-header"><div><span className="admin-mark"><ServerCog size={22} /></span><span><strong>BilingualPDF 管理后台</strong><small>渠道、档位与运行状态</small></span></div><nav><Link className="button secondary" to="/"><ArrowLeft size={17} />用户端</Link><button className="icon-button" title="退出登录" onClick={logout}><LogOut size={18} /></button></nav></header><main className="admin-main">
    <div className="section-heading"><div><span className="eyebrow"><Activity size={15} />服务概况</span><h1>运行与配置</h1></div><button className="button secondary" onClick={cleanup}><Trash2 size={17} />执行保留清理</button></div>
    {usage && <section className="metric-band">{[["任务", "jobs"], ["运行中", "running"], ["成功", "succeeded"], ["失败", "failed"], ["文件", "files"], ["页数", "pages"]].map(([label, key]) => <div key={key}><span>{label}</span><strong>{usage.summary[key] || 0}</strong></div>)}</section>}
    <div className="admin-columns"><div>{profiles.map((profile) => <TierEditor key={profile.slug} initial={profile} isDefault={defaultTier === profile.slug} onSaved={load} onDefault={async () => { await request(`/admin/api/default-tier/${profile.slug}`, { method: "POST" }); load(); }} />)}</div><aside><section className="admin-section"><h2><RotateCcw size={18} />最近失败</h2>{usage?.failures.length ? usage.failures.map((failure, index) => <div className="failure-row" key={index}><strong>{failure.tier === "advanced" ? "高级版" : "普通版"}</strong><p>{failure.error}</p></div>) : <p className="muted">暂无失败记录</p>}</section></aside></div>
  </main></div>;
}
