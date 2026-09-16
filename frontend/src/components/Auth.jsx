import { useEffect, useRef, useState } from "react";
import { Button, Field } from "./ui";
import { ConnectionStatus, LanguageSelect, ThemeToggle } from "./Controls";

const emptyErrors = { email: "", password: "" };

export default function Auth({ t, lang, setLang, theme, setTheme, online, onSubmit }) {
  const [mode, setMode] = useState("login");
  const [credentials, setCredentials] = useState({ email: "", password: "" });
  const [errors, setErrors] = useState(emptyErrors);
  const [formError, setFormError] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [pending, setPending] = useState(false);
  const emailRef = useRef(null);

  useEffect(() => {
    emailRef.current?.focus();
  }, []);

  const switchMode = (next) => {
    setMode(next);
    setErrors(emptyErrors);
    setFormError("");
  };

  const update = (key) => (event) => {
    setCredentials((current) => ({ ...current, [key]: event.target.value }));
    // Clearing on type keeps the error from nagging while the user fixes it.
    if (errors[key]) setErrors((current) => ({ ...current, [key]: "" }));
    if (formError) setFormError("");
  };

  const validate = () => {
    const next = { ...emptyErrors };
    if (!credentials.email.trim()) next.email = t("required");
    if (credentials.password.length < 8) next.password = t("passwordHint");
    setErrors(next);
    return !next.email && !next.password;
  };

  const submit = async (event) => {
    event.preventDefault();
    setFormError("");
    if (!validate()) return;

    setPending(true);
    try {
      await onSubmit(mode, credentials);
    } catch (error) {
      setFormError(error.message);
    } finally {
      setPending(false);
    }
  };

  const cta = mode === "login" ? t("enter") : t("create");
  const pendingCta = mode === "login" ? t("signingIn") : t("creatingWorkspace");

  return (
    <div className="auth-page">
      <div className="auth-top">
        <span className="brand">
          <span className="mark" aria-hidden="true">
            T
          </span>
          <span>
            Trade<span>Miror</span>
          </span>
        </span>
        <div className="auth-controls">
          <ThemeToggle theme={theme} setTheme={setTheme} t={t} />
          <LanguageSelect lang={lang} setLang={setLang} t={t} />
        </div>
      </div>

      <div className="auth-layout">
        <div className="auth-copy">
          <p className="eyebrow">{t("tagline")}</p>
          <h1>
            {t("headline")}
            <br />
            <em>{t("headline2")}</em>
          </h1>
          <p>{t("intro")}</p>
          <div className="principles">
            <span>{t("principle1")}</span>
            <span>{t("principle2")}</span>
            <span>{t("principle3")}</span>
          </div>
        </div>

        <section className="auth-card">
          <p className="eyebrow">{t("access")}</p>
          <h2>{mode === "login" ? t("welcome") : t("createWorkspace")}</h2>

          <div className="tabs">
            <button
              type="button"
              className={mode === "login" ? "active" : ""}
              aria-pressed={mode === "login"}
              onClick={() => switchMode("login")}
            >
              {t("signIn")}
            </button>
            <button
              type="button"
              className={mode === "register" ? "active" : ""}
              aria-pressed={mode === "register"}
              onClick={() => switchMode("register")}
            >
              {t("register")}
            </button>
          </div>

          <form onSubmit={submit} noValidate>
            <Field label={t("email")} error={errors.email}>
              <input
                ref={emailRef}
                type="email"
                inputMode="email"
                autoComplete="email"
                value={credentials.email}
                onChange={update("email")}
                placeholder="you@example.com"
              />
            </Field>

            <Field
              label={t("password")}
              error={errors.password}
              hint={mode === "register" ? t("passwordHint") : undefined}
              affix={
                <button
                  type="button"
                  className="affix-button"
                  onClick={() => setShowPassword((value) => !value)}
                  aria-label={showPassword ? t("hidePassword") : t("showPassword")}
                  title={showPassword ? t("hidePassword") : t("showPassword")}
                >
                  {showPassword ? "◎" : "◉"}
                </button>
              }
            >
              <input
                type={showPassword ? "text" : "password"}
                autoComplete={mode === "login" ? "current-password" : "new-password"}
                value={credentials.password}
                onChange={update("password")}
              />
            </Field>

            <Button type="submit" variant="primary" pending={pending} chevron="→">
              {pending ? pendingCta : cta}
            </Button>
          </form>

          <p className="form-message" role="alert">
            {formError}
          </p>
          <div className="auth-note">
            <ConnectionStatus online={online} t={t} />
          </div>
        </section>
      </div>
    </div>
  );
}
