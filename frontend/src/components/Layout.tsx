import { FileClock, FileText, Languages, Settings, ShieldCheck } from "lucide-react";
import { NavLink, Outlet, useLocation } from "react-router-dom";

const nav = [
  { to: "/", label: "新建翻译", icon: Languages },
  { to: "/history", label: "翻译历史", icon: FileClock },
  { to: "/settings", label: "设置", icon: Settings },
];

export function Layout() {
  const location = useLocation();
  const isAdmin = location.pathname.startsWith("/admin");
  if (isAdmin) return <Outlet />;
  return (
    <div className="app-shell">
      <aside className="sidebar">
        <NavLink to="/" className="brand" aria-label="BilingualPDF 首页">
          <span className="brand-mark"><FileText size={20} /></span>
          <span><strong>BilingualPDF</strong><small>文档翻译工作台</small></span>
        </NavLink>
        <nav aria-label="主要导航">
          {nav.map(({ to, label, icon: Icon }) => (
            <NavLink key={to} to={to} end={to === "/"} className={({ isActive }) => isActive ? "active" : ""}>
              <Icon size={19} /><span>{label}</span>
            </NavLink>
          ))}
        </nav>
        <div className="sidebar-foot"><ShieldCheck size={17} /><span>文件 7 天后自动清理</span></div>
      </aside>
      <main className="main"><Outlet /></main>
      <nav className="mobile-nav" aria-label="移动端导航">
        {nav.map(({ to, label, icon: Icon }) => (
          <NavLink key={to} to={to} end={to === "/"} className={({ isActive }) => isActive ? "active" : ""}>
            <Icon size={20} /><span>{label}</span>
          </NavLink>
        ))}
      </nav>
    </div>
  );
}
