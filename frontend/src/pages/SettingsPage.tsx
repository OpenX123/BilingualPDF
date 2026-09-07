import { CheckCircle2, Eye, EyeOff, KeyRound, Monitor, Moon, Sun, Trash2 } from "lucide-react";
import { useEffect, useState } from "react";

export function SettingsPage() {
  const [key, setKey] = useState(() => localStorage.getItem("bilingualpdf_api_key") || "");
  const [saved, setSaved] = useState(Boolean(key));
  const [visible, setVisible] = useState(false);
  const [theme, setTheme] = useState(() => localStorage.getItem("bilingualpdf_theme") || "system");
  useEffect(() => {
    document.documentElement.dataset.theme = theme;
    localStorage.setItem("bilingualpdf_theme", theme);
  }, [theme]);
  const save = () => { if (key.trim()) localStorage.setItem("bilingualpdf_api_key", key.trim()); setSaved(Boolean(key.trim())); };
  const clear = () => { localStorage.removeItem("bilingualpdf_api_key"); setKey(""); setSaved(false); };
  return <div className="page narrow-page">
    <header className="page-header"><div><span className="eyebrow"><KeyRound size={15} />个人偏好</span><h1>设置</h1><p>这些内容只保存在当前浏览器。</p></div></header>
    <section className="settings-section"><div className="setting-title"><KeyRound size={20} /><div><h2>API Key</h2><p>翻译时安全转发，不会写入任务记录。</p></div>{saved && <span className="saved-state"><CheckCircle2 size={15} />已保存</span>}</div><label className="password-field"><input type={visible ? "text" : "password"} value={key} onChange={(event) => { setKey(event.target.value); setSaved(false); }} placeholder="输入你的 API Key" autoComplete="off" /><button className="icon-button" title={visible ? "隐藏 Key" : "显示 Key"} onClick={() => setVisible(!visible)}>{visible ? <EyeOff size={18} /> : <Eye size={18} />}</button></label><div className="button-row"><button className="button primary" disabled={!key.trim()} onClick={save}>保存 Key</button><button className="button secondary" disabled={!key && !saved} onClick={clear}><Trash2 size={17} />清除已保存 Key</button></div></section>
    <section className="settings-section"><div className="setting-title"><Monitor size={20} /><div><h2>主题</h2><p>选择适合当前环境的显示模式。</p></div></div><div className="segmented icon-segments"><button className={theme === "light" ? "selected" : ""} onClick={() => setTheme("light")}><Sun size={17} />浅色</button><button className={theme === "dark" ? "selected" : ""} onClick={() => setTheme("dark")}><Moon size={17} />深色</button><button className={theme === "system" ? "selected" : ""} onClick={() => setTheme("system")}><Monitor size={17} />跟随系统</button></div></section>
  </div>;
}
