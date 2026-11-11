/**
 * Formats numbers into Indian Rupee (₹) currency format.
 * Supports compact notation (Crores, Lakhs) and full standard Indian numbering format.
 */

export function formatINR(val, compact = true) {
  if (val === null || val === undefined || isNaN(val)) return "₹0";
  const num = Number(val);
  const abs = Math.abs(num);

  if (compact) {
    if (abs >= 10000000) {
      // 1 Crore = 10,000,000 (10^7)
      const formatted = (abs / 10000000).toFixed(2);
      return `${num < 0 ? "-" : ""}₹${formatted} Cr`;
    }
    if (abs >= 100000) {
      // 1 Lakh = 100,000 (10^5)
      const formatted = (abs / 100000).toFixed(2);
      return `${num < 0 ? "-" : ""}₹${formatted} L`;
    }
    if (abs >= 1000) {
      const formatted = (abs / 1000).toFixed(1);
      return `${num < 0 ? "-" : ""}₹${formatted} K`;
    }
  }

  return new Intl.NumberFormat("en-IN", {
    style: "currency",
    currency: "INR",
    maximumFractionDigits: 0,
  }).format(num);
}

export function formatINRPrecise(val) {
  if (val === null || val === undefined || isNaN(val)) return "₹0";
  return new Intl.NumberFormat("en-IN", {
    style: "currency",
    currency: "INR",
    maximumFractionDigits: 2,
  }).format(Number(val));
}
