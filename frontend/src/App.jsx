import { useCallback, useEffect, useMemo, useState } from "react";
import { api, ApiError, clearToken, readToken, writeToken } from "./lib/api";
import { translate } from "./lib/i18n";
import { useLanguage, useTheme } from "./lib/preferences";
import { Button, useToast } from "./components/ui";
import { ConnectionStatus, LanguageSelect, ThemeToggle } from "./components/Controls";
import Auth from "./components/Auth";
import Dashboard from "./components/Dashboard";
import Accounts from "./components/Accounts";
import AccountDetail from "./components/AccountDetail";
import Profile from "./components/Profile";

const VIEWS = {
  dashboard: { icon: "◈", key: "overview" },
  accounts: { icon: "▣", key: "accounts" },
  profile: { icon: "◎", key: "profile" },
};

export default function App() {
  const [lang, setLang] = useLanguage();
  const [theme, setTheme] = useTheme();
  const t = useCallback((key, vars) => translate(lang, key, vars), [lang]);
  const toast = useToast();

  const [token, setToken] = useState(readToken);
  const [user, setUser] = useState(null);
  const [accounts, setAccounts] = useState([]);
  const [tradesByAccount, setTradesByAccount] = useState({});
  const [riskProfiles, setRiskProfiles] = useState({});
  const [riskAssessmentsByTrade, setRiskAssessmentsByTrade] = useState({});
  const [instruments, setInstruments] = useState([]);
  const [booting, setBooting] = useState(Boolean(readToken()));
  const [loadingData, setLoadingData] = useState(false);
  const [online, setOnline] = useState(null);
  const [view, setView] = useState("dashboard");
  const [selectedId, setSelectedId] = useState(null);

  const selected = useMemo(
    () => accounts.find((account) => account.id === selectedId) || null,
    [accounts, selectedId],
  );

  const checkHealth = useCallback(async () => {
    setOnline(null);
    try {
      await api("/health");
      setOnline(true);
      return true;
    } catch {
      setOnline(false);
      return false;
    }
  }, []);

  const signOut = useCallback(() => {
    clearToken();
    setToken(null);
    setUser(null);
    setAccounts([]);
    setTradesByAccount({});
    setRiskProfiles({});
    setRiskAssessmentsByTrade({});
    setSelectedId(null);
    setView("dashboard");
  }, []);

  useEffect(() => {
    checkHealth();
  }, [checkHealth]);

  // One pass on sign-in: identity, accounts, then every account's journal so the
  // dashboard can show real totals instead of placeholders.
  useEffect(() => {
    if (!token) {
      setBooting(false);
      return;
    }

    let cancelled = false;
    setLoadingData(true);

    (async () => {
      try {
        // Reference data rides along with identity; losing it must not end the session.
        const [profile, catalog] = await Promise.all([
          api("/api/v1/auth/me", {}, token),
          api("/api/v1/instruments/").catch(() => []),
        ]);
        if (cancelled) return;
        setUser(profile);
        setInstruments(catalog);

        const list = await api("/api/v1/accounts/", {}, token);
        if (cancelled) return;
        setAccounts(list);

        const profiles = await Promise.all(
          list.map((account) =>
            api(`/api/v1/accounts/${account.id}/risk-profile`, {}, token)
              .then((profile) => [account.id, profile])
              .catch(() => [account.id, null]),
          ),
        );
        if (cancelled) return;
        setRiskProfiles(Object.fromEntries(profiles));

        const journals = await Promise.all(
          list.map((account) =>
            api(`/api/v1/accounts/${account.id}/trades`, {}, token)
              .then((trades) => [account.id, trades])
              .catch(() => [account.id, []]),
          ),
        );
        if (cancelled) return;
        setTradesByAccount(Object.fromEntries(journals));
      } catch (error) {
        if (cancelled) return;
        // A dead token is the common case; anything else leaves the session alone.
        if (error instanceof ApiError && error.status === 401) signOut();
        else if (error instanceof ApiError && error.status === 0) setOnline(false);
      } finally {
        if (!cancelled) {
          setBooting(false);
          setLoadingData(false);
        }
      }
    })();

    return () => {
      cancelled = true;
    };
  }, [token, signOut]);

  const friendlyError = useCallback(
    (error, mode) => {
      if (!(error instanceof ApiError)) return error;
      if (error.status === 0) return new Error(t("networkError"));
      if (mode === "login" && error.status === 401) return new Error(t("invalidCredentials"));
      if (mode === "register" && (error.status === 400 || error.status === 409)) {
        return new Error(t("emailTaken"));
      }
      return error;
    },
    [t],
  );

  const authenticate = async (mode, credentials) => {
    try {
      if (mode === "register") {
        await api("/api/v1/auth/register", { method: "POST", body: JSON.stringify(credentials) });
      }
      const session = await api("/api/v1/auth/login", { method: "POST", body: JSON.stringify(credentials) });
      writeToken(session.access_token);
      setBooting(true);
      setToken(session.access_token);
      setOnline(true);
    } catch (error) {
      throw friendlyError(error, mode);
    }
  };

  const createAccount = async (payload) => {
    try {
      const created = await api("/api/v1/accounts/", { method: "POST", body: JSON.stringify(payload) }, token);
      setAccounts((current) => [created, ...current]);
      setTradesByAccount((current) => ({ ...current, [created.id]: [] }));
      toast(t("created"));
      return created;
    } catch (error) {
      throw friendlyError(error);
    }
  };

  const createTrade = async (payload) => {
    try {
      const created = await api(
        `/api/v1/accounts/${selectedId}/trades`,
        { method: "POST", body: JSON.stringify(payload) },
        token,
      );
      setTradesByAccount((current) => ({
        ...current,
        [selectedId]: [created, ...(current[selectedId] || [])],
      }));
      const assessments = await api(
        `/api/v1/accounts/${selectedId}/trades/${created.id}/risk-assessments`,
        {},
        token,
      ).catch(() => []);
      setRiskAssessmentsByTrade((current) => ({ ...current, [created.id]: assessments }));
      toast(t("tradeCreated"));
      return created;
    } catch (error) {
      throw friendlyError(error);
    }
  };

  const closeTrade = async (trade, exitPrice) => {
    try {
      const closed = await api(
        `/api/v1/accounts/${selectedId}/trades/${trade.id}/close`,
        { method: "POST", body: JSON.stringify({ exit_price: exitPrice }) },
        token,
      );
      setTradesByAccount((current) => ({
        ...current,
        [selectedId]: (current[selectedId] || []).map((item) => (item.id === closed.id ? closed : item)),
      }));
      const refreshedAccounts = await api("/api/v1/accounts/", {}, token);
      setAccounts(refreshedAccounts);
      const assessments = await api(
        `/api/v1/accounts/${selectedId}/trades/${closed.id}/risk-assessments`,
        {},
        token,
      ).catch(() => []);
      setRiskAssessmentsByTrade((current) => ({ ...current, [closed.id]: assessments }));
      toast(t("closed"));
      return closed;
    } catch (error) {
      throw friendlyError(error);
    }
  };

  const saveRiskProfile = async (accountId, payload) => {
    try {
      const profile = await api(
        `/api/v1/accounts/${accountId}/risk-profile`,
        { method: "PUT", body: JSON.stringify(payload) },
        token,
      );
      setRiskProfiles((current) => ({ ...current, [accountId]: profile }));
      toast(t("riskProfileSaved"));
      return profile;
    } catch (error) {
      throw friendlyError(error);
    }
  };

  const loadRiskAssessments = async (accountId, tradeId) => {
    const assessments = await api(
      `/api/v1/accounts/${accountId}/trades/${tradeId}/risk-assessments`,
      {},
      token,
    );
    setRiskAssessmentsByTrade((current) => ({ ...current, [tradeId]: assessments }));
    return assessments;
  };

  // The panel renders from the cached row first, then swaps in the server's copy.
  const loadTrade = async (tradeId) => {
    try {
      const detail = await api(`/api/v1/accounts/${selectedId}/trades/${tradeId}`, {}, token);
      setTradesByAccount((current) => ({
        ...current,
        [selectedId]: (current[selectedId] || []).map((item) => (item.id === detail.id ? detail : item)),
      }));
      return detail;
    } catch (error) {
      throw friendlyError(error);
    }
  };

  const openAccount = (account) => {
    setSelectedId(account.id);
    setView("detail");
  };

  const go = (next) => {
    setView(next);
    if (next !== "detail") setSelectedId(null);
  };

  if (booting) {
    return (
      <div className="boot">
        <span className="mark" aria-hidden="true">
          T
        </span>
        <p>{t("loading")}</p>
      </div>
    );
  }

  if (!user) {
    return (
      <Auth
        t={t}
        lang={lang}
        setLang={setLang}
        theme={theme}
        setTheme={setTheme}
        online={online}
        onSubmit={authenticate}
      />
    );
  }

  const title =
    view === "dashboard"
      ? t("dashboard")
      : view === "accounts"
        ? t("yourAccounts")
        : view === "detail"
          ? selected?.name || t("accounts")
          : t("profile");

  return (
    <div className="app-shell">
      <a className="skip-link" href="#main">
        {t("skipToContent")}
      </a>

      <aside className="sidebar">
        <button type="button" className="brand" onClick={() => go("dashboard")}>
          <span className="mark" aria-hidden="true">
            T
          </span>
          <span>
            Trade<span>Miror</span>
          </span>
        </button>

        <p className="side-label">{t("workspace")}</p>

        <nav aria-label={t("workspace")}>
          {Object.entries(VIEWS).map(([name, meta]) => {
            const active = name === view || (name === "accounts" && view === "detail");
            return (
              <button
                key={name}
                type="button"
                className={`nav-item ${active ? "active" : ""}`}
                aria-current={active ? "page" : undefined}
                onClick={() => go(name)}
              >
                <span aria-hidden="true">{meta.icon}</span>
                <em>{t(meta.key)}</em>
                {name === "accounts" && accounts.length > 0 && <small>{accounts.length}</small>}
              </button>
            );
          })}
        </nav>

        <div className="sidebar-bottom">
          <button type="button" className="nav-item" onClick={signOut}>
            <span aria-hidden="true">↪</span>
            <em>{t("logout")}</em>
          </button>
        </div>
      </aside>

      <div className="content">
        <header className="topbar">
          <div>
            <p className="eyebrow">{t("workspace")}</p>
            <h1>{title}</h1>
          </div>
          <div className="header-right">
            <ConnectionStatus online={online} t={t} />
            <ThemeToggle theme={theme} setTheme={setTheme} t={t} />
            <LanguageSelect lang={lang} setLang={setLang} t={t} />
            <div className="avatar" title={user.email}>
              {user.email[0].toUpperCase()}
            </div>
          </div>
        </header>

        {online === false && (
          <div className="offline-banner" role="alert">
            <div>
              <strong>{t("offlineTitle")}</strong>
              <p>{t("offlineText")}</p>
            </div>
            <Button variant="secondary" className="compact" onClick={checkHealth}>
              {t("retry")}
            </Button>
          </div>
        )}

        <main id="main" tabIndex={-1}>
          {view === "dashboard" && (
            <Dashboard
              t={t}
              lang={lang}
              user={user}
              accounts={accounts}
              tradesByAccount={tradesByAccount}
              loading={loadingData}
              go={go}
              open={openAccount}
            />
          )}
          {view === "accounts" && (
            <Accounts
              t={t}
              lang={lang}
              accounts={accounts}
              tradesByAccount={tradesByAccount}
              loading={loadingData}
              open={openAccount}
              onCreate={createAccount}
            />
          )}
          {view === "detail" && selected && (
            <AccountDetail
              t={t}
              lang={lang}
              account={selected}
              trades={tradesByAccount[selected.id]}
              riskProfile={riskProfiles[selected.id]}
              riskAssessmentsByTrade={riskAssessmentsByTrade}
              loading={loadingData && !tradesByAccount[selected.id]}
              back={() => go("accounts")}
              instruments={instruments}
              onCreateTrade={createTrade}
              onCloseTrade={closeTrade}
              onLoadTrade={loadTrade}
              onSaveRiskProfile={saveRiskProfile}
              onLoadRiskAssessments={(tradeId) => loadRiskAssessments(selected.id, tradeId)}
            />
          )}
          {view === "profile" && (
            <Profile
              t={t}
              lang={lang}
              setLang={setLang}
              theme={theme}
              setTheme={setTheme}
              user={user}
              accounts={accounts}
              onLogout={signOut}
            />
          )}
        </main>
      </div>
    </div>
  );
}
