import { LANGUAGES } from "../lib/i18n";
import { THEMES } from "../lib/preferences";

const THEME_ICON = { system: "◐", light: "☀", dark: "☾" };

export function LanguageSelect({ lang, setLang, t }) {
  return (
    <label className="language-wrap">
      <span className="sr-only">{t("language")}</span>
      <select className="language" value={lang} onChange={(event) => setLang(event.target.value)}>
        {LANGUAGES.map((option) => (
          <option key={option.value} value={option.value}>
            {option.label}
          </option>
        ))}
      </select>
    </label>
  );
}

/** Compact cycle button: system → light → dark → system. */
export function ThemeToggle({ theme, setTheme, t }) {
  const next = THEMES[(THEMES.indexOf(theme) + 1) % THEMES.length];
  const label = `${t("theme")}: ${t(`theme${theme[0].toUpperCase()}${theme.slice(1)}`)}`;

  return (
    <button type="button" className="theme-toggle" onClick={() => setTheme(next)} aria-label={label} title={label}>
      <span aria-hidden="true">{THEME_ICON[theme]}</span>
    </button>
  );
}

export function ConnectionStatus({ online, t, compact }) {
  const state = online === null ? "checking" : online ? "online" : "offline";
  const label = online === null ? t("checking") : online ? t("connected") : t("disconnected");

  return (
    <span className={`status ${state} ${compact ? "compact" : ""}`} title={label}>
      <i aria-hidden="true" />
      <span className={compact ? "sr-only" : ""}>{label}</span>
    </span>
  );
}
