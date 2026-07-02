import { NavLink, Route, Routes } from "react-router-dom";
import Home from "./pages/Home.jsx";
import GeneralPractice from "./pages/GeneralPractice.jsx";
import ToeflPractice from "./pages/ToeflPractice.jsx";
import History from "./pages/History.jsx";
import SessionDetail from "./pages/SessionDetail.jsx";
import Settings from "./pages/Settings.jsx";

export default function App() {
  return (
    <>
      <nav className="topnav">
        <span className="brand">🗣️ Speaking Coach</span>
        <NavLink to="/" end>
          Home
        </NavLink>
        <NavLink to="/general">General Practice</NavLink>
        <NavLink to="/toefl">TOEFL Practice</NavLink>
        <NavLink to="/history">History</NavLink>
        <NavLink to="/settings">Settings</NavLink>
      </nav>
      <Routes>
        <Route path="/" element={<Home />} />
        <Route path="/general" element={<GeneralPractice />} />
        <Route path="/toefl" element={<ToeflPractice />} />
        <Route path="/history" element={<History />} />
        <Route path="/history/:id" element={<SessionDetail />} />
        <Route path="/settings" element={<Settings />} />
      </Routes>
    </>
  );
}
