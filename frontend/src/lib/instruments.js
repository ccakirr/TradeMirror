/** Decimal places implied by a step the API sends as a string, e.g. "0.0001" → 4. */
export function stepDecimals(step) {
  const text = String(step ?? "");
  const dot = text.indexOf(".");
  return dot === -1 ? 0 : text.length - dot - 1;
}

const PLAIN_DECIMAL = /^[+-]?(\d+(\.\d*)?|\.\d+)$/;
const EXPONENTIAL = /^([+-]?)(\d*)(?:\.(\d*))?[eE]([+-]?\d+)$/;

/**
 * "1e-5" → "0.00001". A number input accepts the exponent form, so it reaches
 * us from real typing; shifting the point keeps the digits exact.
 */
function expandExponent(text) {
  const match = EXPONENTIAL.exec(text);
  if (!match) return null;

  const [, sign, whole = "", fraction = "", exponent] = match;
  const digits = whole + fraction;
  // Anything beyond this is not a price someone meant to type.
  if (!digits || Math.abs(Number(exponent)) > 30) return null;

  const point = whole.length + Number(exponent);
  if (point <= 0) return `${sign}0.${"0".repeat(-point)}${digits}`;
  if (point >= digits.length) return `${sign}${digits}${"0".repeat(point - digits.length)}`;
  return `${sign}${digits.slice(0, point)}.${digits.slice(point)}`;
}

/**
 * Exact decimal string → scaled integer, rounding half away from zero.
 * Binary floats get 1.10855 wrong at exactly this boundary, so the digits are
 * read as written instead of going through Number.
 */
function scaleDecimalString(text, decimals) {
  const trimmed = text.trim();
  const negative = trimmed.startsWith("-");
  const [intPart = "", fracPart = ""] = trimmed.replace(/^[+-]/, "").split(".");
  const padded = fracPart.padEnd(decimals + 1, "0");

  let scaled = BigInt((intPart || "0") + padded.slice(0, decimals));
  if (padded.charCodeAt(decimals) - 48 >= 5) scaled += 1n;

  return negative ? -scaled : scaled;
}

/** Integer division rounding half away from zero. */
function divideRounded(value, divisor) {
  return (2n * value + (value < 0n ? -divisor : divisor)) / (2n * divisor);
}

function renderScaled(scaled, decimals) {
  const negative = scaled < 0n;
  const digits = (negative ? -scaled : scaled).toString().padStart(decimals + 1, "0");
  const whole = decimals ? digits.slice(0, -decimals) : digits;
  const fraction = decimals ? `.${digits.slice(-decimals)}` : "";
  return `${negative ? "-" : ""}${whole}${fraction}`;
}

/**
 * Snap a typed number onto the instrument's increment and render it at that
 * precision — the format the API will accept, produced before it is asked for.
 * Handles steps that are not powers of ten (0.25, say) as well as the ones the
 * catalog ships today.
 */
export function quantize(raw, step) {
  if (raw === "" || raw === null || raw === undefined) return "";

  const original = String(raw);
  const text = PLAIN_DECIMAL.test(original.trim())
    ? original.trim()
    : expandExponent(original.trim());
  const decimals = stepDecimals(step);

  // Anything still unreadable is left for the server to reject.
  if (text === null || !PLAIN_DECIMAL.test(String(step).trim())) return original;

  const increment = scaleDecimalString(String(step), decimals);
  if (increment <= 0n) return original;

  const value = scaleDecimalString(text, decimals);
  return renderScaled(divideRounded(value, increment) * increment, decimals);
}

export const CATEGORY_KEYS = {
  crypto: "catCrypto",
  forex: "catForex",
  metal: "catMetal",
  index: "catIndex",
  stock: "catStock",
  energy: "catEnergy",
};
