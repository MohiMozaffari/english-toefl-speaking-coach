import { Suspense, lazy } from "react";
import { Route, Routes } from "react-router-dom";
import Layout from "./components/Layout";
import { LoadingCard } from "./components/ui";

// Route-level code splitting keeps the initial bundle small.
const Dashboard = lazy(() => import("./pages/Dashboard"));
const GeneralPractice = lazy(() => import("./pages/GeneralPractice"));
const ToeflPractice = lazy(() => import("./pages/ToeflPractice"));
const Reading = lazy(() => import("./pages/Reading"));
const WritingPractice = lazy(() => import("./pages/WritingPractice"));
const Shadowing = lazy(() => import("./pages/Shadowing"));
const PronunciationLab = lazy(() => import("./pages/PronunciationLab"));
const Listening = lazy(() => import("./pages/Listening"));
const History = lazy(() => import("./pages/History"));
const SessionDetail = lazy(() => import("./pages/SessionDetail"));
const Settings = lazy(() => import("./pages/Settings"));

export default function App() {
  return (
    <Routes>
      <Route element={<Layout />}>
        <Route
          path="/"
          element={
            <Suspense fallback={<LoadingCard lines={4} />}>
              <Dashboard />
            </Suspense>
          }
        />
        {[
          ["/general", GeneralPractice],
          ["/toefl", ToeflPractice],
          ["/reading", Reading],
          ["/writing", WritingPractice],
          ["/shadowing", Shadowing],
          ["/pronunciation", PronunciationLab],
          ["/listening", Listening],
          ["/history", History],
          ["/history/:id", SessionDetail],
          ["/settings", Settings],
        ].map(([path, Page]) => (
          <Route
            key={path as string}
            path={path as string}
            element={
              <Suspense fallback={<LoadingCard lines={4} />}>
                {(() => {
                  const P = Page as React.LazyExoticComponent<() => JSX.Element>;
                  return <P />;
                })()}
              </Suspense>
            }
          />
        ))}
      </Route>
    </Routes>
  );
}
