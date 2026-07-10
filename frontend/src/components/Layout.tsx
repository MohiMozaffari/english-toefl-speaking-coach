import { useEffect, useState } from "react";
import { NavLink, Outlet, useLocation } from "react-router-dom";
import { useTheme } from "../contexts";

const NAV = [
  { section: "Overview", items: [{ to: "/", icon: "📊", label: "Dashboard" }] },
  {
    section: "Practice",
    items: [
      { to: "/toefl", icon: "🎓", label: "TOEFL Speaking" },
      { to: "/reading", icon: "📖", label: "TOEFL Reading" },
      { to: "/writing", icon: "✍️", label: "TOEFL Writing" },
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

// Bottom tab bar: 4 most-used sections stay one tap away; everything else
// (including theme) lives behind "More", which opens a bottom sheet.
const BOTTOM_TABS = [
  { to: "/", icon: "📊", label: "Home" },
  { to: "/toefl", icon: "🎓", label: "TOEFL" },
  { to: "/shadowing", icon: "🗣️", label: "Shadow" },
  { to: "/history", icon: "🕘", label: "History" },
];

const MORE_LINKS = [
  { to: "/reading", icon: "📖", label: "TOEFL Reading" },
  { to: "/writing", icon: "✍️", label: "TOEFL Writing" },
  { to: "/general", icon: "🗨️", label: "General English" },
  { to: "/pronunciation", icon: "👄", label: "Pronunciation Lab" },
  { to: "/listening", icon: "🎧", label: "Listening" },
  { to: "/settings", icon: "⚙️", label: "Settings" },
];

export default function Layout() {
  const [moreOpen, setMoreOpen] = useState(false);
  const { theme, toggleTheme } = useTheme();
  const location = useLocation();

  useEffect(() => {
    setMoreOpen(false);
  }, [location.pathname]);

  return (
    <div className="shell">
      <div className="mobile-topbar">
        <span className="brand">🗣️ Speaking Coach</span>
      </div>

      <nav className="sidebar" aria-label="Main navigation">
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

      <main className="content" data-section={location.pathname.split("/")[1] || "dashboard"} key={location.pathname}>
        <Outlet />
      </main>

      <nav className="bottom-nav" aria-label="Main navigation">
        {BOTTOM_TABS.map((item) => (
          <NavLink
            key={item.to}
            to={item.to}
            end={item.to === "/"}
            className={({ isActive }) => `bottom-nav-link ${isActive ? "active" : ""}`}
          >
            <span className="icon" aria-hidden="true">{item.icon}</span>
            {item.label}
          </NavLink>
        ))}
        <button
          type="button"
          className={`bottom-nav-link ${moreOpen ? "active" : ""}`}
          onClick={() => setMoreOpen(true)}
          aria-label="More sections"
        >
          <span className="icon" aria-hidden="true">☰</span>
          More
        </button>
      </nav>

      {moreOpen && (
        <div className="more-sheet">
          <button type="button" className="backdrop" aria-label="Close menu" onClick={() => setMoreOpen(false)} />
          <div className="more-sheet-panel">
            <div className="more-sheet-handle" />
            {MORE_LINKS.map((item) => (
              <NavLink
                key={item.to}
                to={item.to}
                className={({ isActive }) => `more-sheet-link ${isActive ? "active" : ""}`}
              >
                <span className="icon" aria-hidden="true">{item.icon}</span>
                {item.label}
              </NavLink>
            ))}
            <button type="button" className="more-sheet-link" onClick={toggleTheme}>
              <span className="icon" aria-hidden="true">{theme === "dark" ? "☀️" : "🌙"}</span>
              {theme === "dark" ? "Light mode" : "Dark mode"}
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
