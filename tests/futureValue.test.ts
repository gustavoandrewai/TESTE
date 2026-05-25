import { describe, expect, it } from "vitest";
import { annualToMonthlyRate, calculateFutureValue } from "../src/lib/futureValue";

describe("future value", () => {
  it("sem taxa", () => {
    const result = calculateFutureValue({ returnRatePeriod: "monthly", termUnit: "months", contributionTiming: "end", inflationEnabled: false, inflationType: "manual", termValue: 12, monthlyContribution: 100, presentValue: 0, returnRatePercent: 0 });
    expect(result.futureValueNominal).toBeCloseTo(1200, 8);
  });

  it("com taxa mensal", () => {
    const result = calculateFutureValue({ returnRatePeriod: "monthly", termUnit: "months", contributionTiming: "end", inflationEnabled: false, inflationType: "manual", termValue: 12, monthlyContribution: 100, presentValue: 0, returnRatePercent: 1 });
    expect(result.futureValueNominal).toBeCloseTo(1268.2503, 3);
  });

  it("converte taxa anual", () => {
    expect(annualToMonthlyRate(0.12)).toBeCloseTo(0.00948879, 8);
  });

  it("com PV e sem PV", () => {
    const withPv = calculateFutureValue({ returnRatePeriod: "monthly", termUnit: "months", contributionTiming: "end", inflationEnabled: false, inflationType: "manual", termValue: 12, monthlyContribution: 0, presentValue: 1000, returnRatePercent: 1 });
    const noPv = calculateFutureValue({ returnRatePeriod: "monthly", termUnit: "months", contributionTiming: "end", inflationEnabled: false, inflationType: "manual", termValue: 12, monthlyContribution: 0, presentValue: 0, returnRatePercent: 1 });
    expect(withPv.futureValueNominal).toBeGreaterThan(noPv.futureValueNominal);
  });

  it("aporte no início maior que no fim", () => {
    const start = calculateFutureValue({ returnRatePeriod: "monthly", termUnit: "months", contributionTiming: "beginning", inflationEnabled: false, inflationType: "manual", termValue: 12, monthlyContribution: 100, presentValue: 0, returnRatePercent: 1 });
    const end = calculateFutureValue({ returnRatePeriod: "monthly", termUnit: "months", contributionTiming: "end", inflationEnabled: false, inflationType: "manual", termValue: 12, monthlyContribution: 100, presentValue: 0, returnRatePercent: 1 });
    expect(start.futureValueNominal).toBeGreaterThan(end.futureValueNominal);
  });

  it("com inflação e sem inflação", () => {
    const withInfl = calculateFutureValue({ returnRatePeriod: "annual", termUnit: "years", contributionTiming: "end", inflationEnabled: true, inflationType: "ipca", inflationAnnualPercent: 4.5, termValue: 10, monthlyContribution: 500, presentValue: 1000, returnRatePercent: 10 });
    const noInfl = calculateFutureValue({ returnRatePeriod: "annual", termUnit: "years", contributionTiming: "end", inflationEnabled: false, inflationType: "ipca", termValue: 10, monthlyContribution: 500, presentValue: 1000, returnRatePercent: 10 });
    expect(withInfl.futureValueReal ?? 0).toBeLessThan(withInfl.futureValueNominal);
    expect(noInfl.futureValueReal).toBeUndefined();
  });
});
