import assert from "node:assert/strict";
import test from "node:test";

import { formatDecisionMetric } from "../frontend/src/utils/decisionFormatting.js";

test("formats percentages consistently with a percent sign", () => {
  assert.equal(formatDecisionMetric("budget_utilization_pct", 101.234), "101.2%");
  assert.equal(formatDecisionMetric("participation_rate", 50), "50.0%");
});

test("formats currency as INR and large counts with separators", () => {
  assert.equal(formatDecisionMetric("allocated_budget", 1234567.5), "₹12,34,567.50");
  assert.equal(formatDecisionMetric("total_publications", 12345), "12,345");
});

test("formats average publications to two decimal places", () => {
  assert.equal(formatDecisionMetric("average_publications_per_faculty", 7.6), "7.60");
});
