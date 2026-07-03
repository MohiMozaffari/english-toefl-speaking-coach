import { createContext, useCallback, useContext, useEffect, useMemo, useState } from "react";
import type { ReactNode } from "react";
import { api } from "./api";
import type { Profile } from "./types";

// --- Theme -----------------------------------------------------------------

type Theme = "dark" | "light";

interface ThemeContextValue {
  theme: Theme;
  toggleTheme: () => void;
}

const ThemeContext = createContext<ThemeContextValue>({ theme: "dark", toggleTheme: () => {} });

function initialTheme(): Theme {
  const stored = localStorage.getItem("theme");
  if (stored === "light" || stored === "dark") return stored;
  return window.matchMedia?.("(prefers-color-scheme: light)").matches ? "light" : "dark";
}

export function ThemeProvider({ children }: { children: ReactNode }) {
  const [theme, setTheme] = useState<Theme>(initialTheme);

  useEffect(() => {
    document.documentElement.dataset.theme = theme;
    localStorage.setItem("theme", theme);
  }, [theme]);

  const toggleTheme = useCallback(() => setTheme((t) => (t === "dark" ? "light" : "dark")), []);
  const value = useMemo(() => ({ theme, toggleTheme }), [theme, toggleTheme]);
  return <ThemeContext.Provider value={value}>{children}</ThemeContext.Provider>;
}

export const useTheme = () => useContext(ThemeContext);

// --- Active profile ------------------------------------------------------------

interface ProfileContextValue {
  profiles: Profile[];
  profile: Profile | null;
  setActiveProfile: (id: number) => void;
  createProfile: (name: string) => Promise<void>;
  refreshProfiles: () => Promise<void>;
}

const ProfileContext = createContext<ProfileContextValue>({
  profiles: [],
  profile: null,
  setActiveProfile: () => {},
  createProfile: async () => {},
  refreshProfiles: async () => {},
});

export function ProfileProvider({ children }: { children: ReactNode }) {
  const [profiles, setProfiles] = useState<Profile[]>([]);
  const [activeId, setActiveId] = useState<number | null>(() => {
    const stored = localStorage.getItem("active_profile_id");
    return stored ? Number(stored) : null;
  });

  const refreshProfiles = useCallback(async () => {
    try {
      const list = await api.getProfiles();
      setProfiles(list);
    } catch {
      // Backend offline — pages surface their own errors; keep the shell usable.
    }
  }, []);

  useEffect(() => {
    refreshProfiles();
  }, [refreshProfiles]);

  const profile = useMemo(() => {
    if (!profiles.length) return null;
    return profiles.find((p) => p.id === activeId) ?? profiles[0];
  }, [profiles, activeId]);

  const setActiveProfile = useCallback((id: number) => {
    setActiveId(id);
    localStorage.setItem("active_profile_id", String(id));
  }, []);

  const createProfile = useCallback(
    async (name: string) => {
      const created = await api.createProfile(name);
      await refreshProfiles();
      setActiveProfile(created.id);
    },
    [refreshProfiles, setActiveProfile]
  );

  const value = useMemo(
    () => ({ profiles, profile, setActiveProfile, createProfile, refreshProfiles }),
    [profiles, profile, setActiveProfile, createProfile, refreshProfiles]
  );
  return <ProfileContext.Provider value={value}>{children}</ProfileContext.Provider>;
}

export const useProfile = () => useContext(ProfileContext);
