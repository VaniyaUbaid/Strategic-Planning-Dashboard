const PERCENTAGE_KEY = /(?:pct|percentage|rate)$/i;
const CURRENCY_KEY = /(?:budget|expenditure|outstanding_fees|grants)/i;
const COUNT_KEY = /(?:publications|faculty|students|count|participants)$/i;

const inrFormatter = new Intl.NumberFormat("en-IN", {
  style: "currency",
  currency: "INR",
  minimumFractionDigits: 2,
  maximumFractionDigits: 2,
});

export function formatDecisionMetric(key, value) {
  if (typeof value !== "number" || !Number.isFinite(value)) return String(value);

  if (PERCENTAGE_KEY.test(key)) {
    return `${value.toLocaleString("en-IN", {
      minimumFractionDigits: 1,
      maximumFractionDigits: 1,
    })}%`;
  }
  if (CURRENCY_KEY.test(key)) return inrFormatter.format(value);
  if (/average|per_faculty/i.test(key)) return value.toLocaleString("en-IN", {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  });
  if (COUNT_KEY.test(key)) return Math.round(value).toLocaleString("en-IN");
  return value.toLocaleString("en-IN", { maximumFractionDigits: 2 });
}
