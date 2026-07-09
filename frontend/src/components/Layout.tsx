import { useEffect, useState } from "react";
import { NavLink, Outlet, useLocation } from "react-router-dom";
import { useTheme } from "../contexts";

const NAV = [
  { section: "Overview", items: [{ to: "/", icon: "📊", label: "Dashboard" }] },
  {
    section: "Practice",
    items: [
      { to: "/toefl", icon: "🎓", label: "TOEFL Speaking" },
      { to: "/general", icon: "🗨️", label: "General English" },
    ],
  },
  {
    section: "Skills",
    items: [
      { to: "/shadowing", icon: "🗣️", label: "Shadowing" },
      { to: "/pronunciation", icon: "👄", label: "Pronunciation Lab" },
      { to: "/listening", icon: "🎧", label: "Listening" },
    ],
  },
  {
    section: "You",
    items: [
      { to: "/history", icon: "🕘", label: "History" },
      { to: "/settings", icon: "⚙️", label: "Settings" },
    ],
  },
];

export default function Layout() {
  const [open, setOpen] = useState(false);
  const { theme, toggleTheme } = useTheme();
  const location = useLocation();

  // Close the mobile drawer on navigation.
  useEffect(() => {
    setOpen(false);
  }, [location.pathname]);

  return (
    <div className="shell">
      <div className="mobile-topbar">
        <button type="button" className="ghost" aria-label="Open menu" onClick={() => setOpen(true)}>
          ☰
        </button>
        <span className="brand">🗣️ Speaking Coach</span>
      </div>

      {open && <button type="button" className="backdrop" aria-label="Close menu" onClick={() => setOpen(false)} />}

      <nav className={`sidebar ${open ? "open" : ""}`} aria-label="Main navigation">
        <div className="brand">🗣️ Speaking Coach</div>
        {NAV.map((group) => (
          <div key={group.section}>
            <div className="nav-section">{group.section}</div>
            {group.items.map((item) => (
              <NavLink key={item.to} to={item.to} end={item.to === "/"} className={({ isActive }) => `nav-link ${isActive ? "active" : ""}`}>
                <span className="icon" aria-hidden="true">{item.icon}</span>
                {item.label}
              </NavLink>
            ))}
          </div>
        ))}
        <div className="sidebar-footer">
          <button type="button" onClick={toggleTheme} aria-label="Toggle color theme">
            {theme === "dark" ? "☀️ Light mode" : "🌙 Dark mode"}
          </button>
        </div>
      </nav>

      <main className="content" key={location.pathname}>
        <Outlet />
      </main>
    </div>
  );
}
