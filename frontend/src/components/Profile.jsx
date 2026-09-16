import { fullDate, money } from "../lib/format";
import { LANGUAGES } from "../lib/i18n";
import { Button, Segmented } from "./ui";

export default function Profile({ t, lang, setLang, theme, setTheme, user, accounts, onLogout }) {
  const total = accounts.reduce((sum, account) => sum + Number(account.current_balance || 0), 0);

  return (
    <>
      <section className="section-head">
        <div>
          <p className="eyebrow">{t("profileTag")}</p>
          <h2>{t("profileTitle")}</h2>
        </div>
      </section>

      <section className="card profile-card">
        <div className="profile-avatar" aria-hidden="true">
          {user.email[0].toUpperCase()}
        </div>
        <div>
          <p className="eyebrow">{t("email")}</p>
          <h3>{user.email}</h3>
          <p className="muted">
            {t("member")} {fullDate(user.created_at, lang)}
          </p>
        </div>
      </section>

      <section className="card preferences-card">
        <p className="eyebrow">{t("preferences")}</p>

        <div className="preference-row">
          <div>
            <h3>{t("theme")}</h3>
            <p className="muted">{t("themeSystem")} · {t("themeLight")} · {t("themeDark")}</p>
          </div>
          <Segmented
            label={t("theme")}
            value={theme}
            onChange={setTheme}
            options={[
              { value: "system", label: t("themeSystem") },
              { value: "light", label: t("themeLight") },
              { value: "dark", label: t("themeDark") },
            ]}
          />
        </div>

        <div className="preference-row">
          <div>
            <h3>{t("language")}</h3>
          </div>
          <Segmented
            label={t("language")}
            value={lang}
            onChange={setLang}
            options={LANGUAGES.map((option) => ({ value: option.value, label: option.label }))}
          />
        </div>

        <div className="preference-row">
          <div>
            <h3>{t("accountsOpen")}</h3>
            <p className="muted">
              {accounts.length} · {money(total, lang)}
            </p>
          </div>
          <Button variant="ghost" className="compact" onClick={onLogout}>
            {t("logout")}
          </Button>
        </div>
      </section>
    </>
  );
}
