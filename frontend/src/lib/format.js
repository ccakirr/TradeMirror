const locales = { en: "en-US", tr: "tr-TR" };
const localeOf = (lang) => locales[lang] || locales.en;

export const money = (value, lang = "en") =>
  new Intl.NumberFormat(localeOf(lang), {
    style: "currency",
    currency: "USD",
    maximumFractionDigits: 2,
  }).format(Number(value || 0));

/** Signed currency, e.g. "+$120.50" — for anything that can win or lose. */
export const signedMoney = (value, lang = "en") => {
  const amount = Number(value || 0);
  return `${amount > 0 ? "+" : ""}${money(amount, lang)}`;
};

export const percent = (value, lang = "en") => {
  const amount = Number(value || 0);
  return `${amount > 0 ? "+" : ""}${new Intl.NumberFormat(localeOf(lang), {
    maximumFractionDigits: 2,
  }).format(amount)}%`;
};

/** Trims trailing zeros so 1.50000000 reads as 1.5 — prices arrive as decimal strings. */
export const price = (value, lang = "en") =>
  new Intl.NumberFormat(localeOf(lang), { maximumFractionDigits: 8 }).format(Number(value || 0));

/** Fixed-digit number in the reader's locale — "2,00" in tr, "2.00" in en. */
export const decimal = (value, lang = "en", digits = 2) =>
  new Intl.NumberFormat(localeOf(lang), {
    minimumFractionDigits: digits,
    maximumFractionDigits: digits,
  }).format(Number(value || 0));

export const shortDate = (value, lang = "en") =>
  new Date(value).toLocaleDateString(localeOf(lang), { day: "2-digit", month: "short" });

export const fullDate = (value, lang = "en") =>
  new Date(value).toLocaleDateString(localeOf(lang), { day: "numeric", month: "long", year: "numeric" });

export const dateTime = (value, lang = "en") =>
  new Date(value).toLocaleString(localeOf(lang), {
    day: "2-digit",
    month: "short",
    hour: "2-digit",
    minute: "2-digit",
  });

const durationUnits = {
  en: { d: "d", h: "h", m: "m" },
  tr: { d: "g", h: "sa", m: "dk" },
};

/** Compact span like "2h 14m"; scalps that close inside a minute read as "<1m". */
export const duration = (ms, lang = "en") => {
  const units = durationUnits[lang] || durationUnits.en;
  const minutes = Math.max(0, Math.floor(Number(ms || 0) / 60000));
  if (!minutes) return `<1${units.m}`;

  const days = Math.floor(minutes / 1440);
  const hours = Math.floor((minutes % 1440) / 60);
  const rest = minutes % 60;

  const parts = [];
  if (days) parts.push(`${days}${units.d}`);
  if (hours) parts.push(`${hours}${units.h}`);
  // Minutes stop being interesting once the position spans days.
  if (rest && !days) parts.push(`${rest}${units.m}`);
  return parts.join(" ");
};

export const sign = (value) => {
  const amount = Number(value || 0);
  if (amount > 0) return "positive";
  if (amount < 0) return "negative";
  return "flat";
};

/** Percentage change between two balances; guards the divide-by-zero. */
export const changePercent = (from, to) => {
  const start = Number(from || 0);
  if (!start) return 0;
  return ((Number(to || 0) - start) / start) * 100;
};
