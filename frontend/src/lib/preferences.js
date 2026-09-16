import { useCallback, useEffect, useState } from "react";

const THEME_KEY = "trademirror_theme";
const LANG_KEY = "trademirror_language";

export const THEMES = ["system", "light", "dark"];

const read = (key, fallback) => {
  try {
    return localStorage.getItem(key) || fallback;
  } catch {
    return fallback;
  }
};

const write = (key, value) => {
  try {
    localStorage.setItem(key, value);
  } catch {
    /* private mode — the choice just won't survive a reload */
  }
};

export function useTheme() {
  const [theme, setTheme] = useState(() => {
    const stored = read(THEME_KEY, "system");
    return THEMES.includes(stored) ? stored : "system";
  });

  useEffect(() => {
    const root = document.documentElement;
    if (theme === "system") delete root.dataset.theme;
    else root.dataset.theme = theme;
  }, [theme]);

  const change = useCallback((value) => {
    write(THEME_KEY, value);
    setTheme(value);
  }, []);

  return [theme, change];
}

export function useLanguage() {
  const [lang, setLang] = useState(() => (read(LANG_KEY, "en") === "tr" ? "tr" : "en"));

  // Keeps <html lang> honest for screen readers and browser translation.
  useEffect(() => {
    document.documentElement.lang = lang;
  }, [lang]);

  const change = useCallback((value) => {
    write(LANG_KEY, value);
    setLang(value);
  }, []);

  return [lang, change];
}
