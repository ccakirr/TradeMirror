import { useMemo, useRef, useState } from "react";
import { summarize } from "../lib/trades";
import { planBadge } from "../lib/plan";
import { Button, EmptyState, Field, Skeleton } from "./ui";
import AccountCard from "./AccountCard";

const emptyForm = { name: "", initial_balance: "" };

export default function Accounts({ t, lang, accounts, tradesByAccount, plansByAccount = {}, loading, open, onCreate }) {
  const [form, setForm] = useState(emptyForm);
  const [errors, setErrors] = useState({});
  const [pending, setPending] = useState(false);
  const [query, setQuery] = useState("");
  const nameRef = useRef(null);

  const filtered = useMemo(() => {
    const term = query.trim().toLowerCase();
    if (!term) return accounts;
    return accounts.filter((account) => account.name.toLowerCase().includes(term));
  }, [accounts, query]);

  const update = (key) => (event) => {
    setForm((current) => ({ ...current, [key]: event.target.value }));
    if (errors[key]) setErrors((current) => ({ ...current, [key]: "" }));
  };

  const submit = async (event) => {
    event.preventDefault();
    const next = {};
    if (form.name.trim().length < 3) next.name = t("nameTooShort");
    if (!(Number(form.initial_balance) > 0)) next.initial_balance = t("balancePositive");
    setErrors(next);
    if (Object.keys(next).length) return;

    setPending(true);
    try {
      await onCreate({ name: form.name.trim(), initial_balance: Number(form.initial_balance) });
      setForm(emptyForm);
      setQuery("");
      nameRef.current?.focus();
    } catch (error) {
      setErrors({ form: error.message });
    } finally {
      setPending(false);
    }
  };

  return (
    <>
      <section className="section-head accounts-head">
        <div>
          <p className="eyebrow">{t("accountStructure")}</p>
          <h2>{t("everyAccount")}</h2>
          <p className="muted">{t("structureText")}</p>
        </div>
        {accounts.length > 3 && (
          <div className="search">
            <input
              type="search"
              value={query}
              onChange={(event) => setQuery(event.target.value)}
              placeholder={t("searchAccounts")}
              aria-label={t("searchAccounts")}
            />
          </div>
        )}
      </section>

      <div className="accounts-layout">
        <div>
          {loading && !accounts.length ? (
            <div className="account-grid">
              {[0, 1].map((key) => (
                <div className="account-card skeleton-card" key={key}>
                  <Skeleton width={31} height={31} radius={99} />
                  <Skeleton width="70%" height={19} />
                  <Skeleton width="40%" height={10} />
                  <Skeleton width="55%" height={25} />
                </div>
              ))}
            </div>
          ) : filtered.length ? (
            <div className="account-grid">
              {filtered.map((account) => (
                <AccountCard
                  key={account.id}
                  account={account}
                  summary={tradesByAccount[account.id] ? summarize(tradesByAccount[account.id]) : undefined}
                  plan={planBadge(
                    plansByAccount[account.id],
                    tradesByAccount[account.id],
                    account.current_balance,
                  )}
                  t={t}
                  lang={lang}
                  onClick={() => open(account)}
                />
              ))}
            </div>
          ) : accounts.length ? (
            <EmptyState
              icon="⌕"
              title={t("noMatches", { query: query.trim() })}
              action={
                <Button variant="secondary" onClick={() => setQuery("")}>
                  {t("clearSearch")}
                </Button>
              }
            />
          ) : (
            <EmptyState title={t("noAccounts")} text={t("structureText")} />
          )}
        </div>

        <section className="card create-card">
          <p className="eyebrow">{t("newAccount")}</p>
          <h2>{t("createSpace")}</h2>
          <p className="muted">{t("addText")}</p>

          <form onSubmit={submit} noValidate>
            <Field label={t("name")} error={errors.name}>
              <input
                ref={nameRef}
                value={form.name}
                onChange={update("name")}
                maxLength="64"
                placeholder={t("namePlaceholder")}
                autoComplete="off"
              />
            </Field>
            <Field label={t("balance")} error={errors.initial_balance}>
              <input
                type="number"
                inputMode="decimal"
                value={form.initial_balance}
                onChange={update("initial_balance")}
                min="0.01"
                step="0.01"
                placeholder="10000"
              />
            </Field>
            <Button type="submit" variant="primary" pending={pending} chevron="→">
              {pending ? t("saving") : t("createAccount")}
            </Button>
          </form>

          {errors.form && (
            <p className="form-message" role="alert">
              {errors.form}
            </p>
          )}
        </section>
      </div>
    </>
  );
}
