import { decimal, money } from "./format";

/** Each value a finding carries has its own shape: money, percent, ratio or days. */
const FORMATTERS = {
  risk: (value, lang) => money(value, lang),
  loss: (value, lang) => money(value, lang),
  planned: (value, lang) => money(value, lang),
  pct: (value, lang) => decimal(value, lang, 2),
  limit: (value, lang) => decimal(value, lang, 2),
  ratio: (value, lang) => decimal(value, lang, 2),
  days: (value, lang) => decimal(value, lang, 1),
  average: (value, lang) => decimal(value, lang, 1),
  score: (value, lang) => decimal(value, lang, 3),
  threshold: (value, lang) => decimal(value, lang, 3),
};

export const VERDICT_KEYS = {
  low: "riskVerdictLow",
  medium: "riskVerdictMedium",
  high: "riskVerdictHigh",
};

/**
 * The backend ships the rule that fired plus its raw numbers; the sentence is
 * written here so both languages read naturally.
 */
export function findingText(t, lang, finding) {
  const values = Object.entries(finding.values || {}).reduce((result, [name, value]) => {
    const format = FORMATTERS[name];
    return { ...result, [name]: format ? format(value, lang) : value };
  }, {});

  return t(`f_${finding.code}`, values);
}
