export type RatePeriod = "monthly" | "annual";
export type TermUnit = "months" | "years";
export type ContributionTiming = "beginning" | "end";
export type InflationIndex = "ipca" | "igpm" | "manual";

export interface CalculatorInput {
  presentValue?: number;
  monthlyContribution?: number;
  returnRatePercent?: number;
  returnRatePeriod: RatePeriod;
  termValue?: number;
  termUnit: TermUnit;
  contributionTiming: ContributionTiming;
  inflationEnabled: boolean;
  inflationType: InflationIndex;
  inflationAnnualPercent?: number;
}

export interface MonthlyRow {
  month: number;
  startingBalance: number;
  contribution: number;
  interest: number;
  endingBalanceNominal: number;
  endingBalanceReal?: number;
  totalInvested: number;
}

export interface CalculatorResult {
  months: number;
  monthlyReturnRate: number;
  monthlyInflationRate: number;
  futureValueNominal: number;
  futureValueReal?: number;
  totalInvested: number;
  totalNominalEarnings: number;
  totalRealEarnings?: number;
  purchasingPowerLoss?: number;
  nominalReturnAccumulated: number;
  realReturnAccumulated?: number;
  schedule: MonthlyRow[];
}

const toNumber = (value: unknown, fallback = 0): number => {
  const parsed = Number(value);
  return Number.isFinite(parsed) ? parsed : fallback;
};

export const annualToMonthlyRate = (annualRate: number): number => Math.pow(1 + annualRate, 1 / 12) - 1;

export const toMonthlyRate = (ratePercent: number, period: RatePeriod): number => {
  const decimalRate = toNumber(ratePercent) / 100;
  return period === "annual" ? annualToMonthlyRate(decimalRate) : decimalRate;
};

export const toMonths = (termValue: number, termUnit: TermUnit): number => {
  const safeTerm = Math.max(0, Math.floor(toNumber(termValue)));
  return termUnit === "years" ? safeTerm * 12 : safeTerm;
};

export const calculateFutureValue = (input: CalculatorInput): CalculatorResult => {
  const presentValue = toNumber(input.presentValue, 0);
  const monthlyContribution = toNumber(input.monthlyContribution, 0);
  const months = toMonths(input.termValue ?? 0, input.termUnit);
  const monthlyReturnRate = toMonthlyRate(input.returnRatePercent ?? 0, input.returnRatePeriod);

  const annualInflationRate = toNumber(input.inflationAnnualPercent, 0) / 100;
  const monthlyInflationRate = input.inflationEnabled ? annualToMonthlyRate(annualInflationRate) : 0;

  const schedule: MonthlyRow[] = [];
  let balance = presentValue;

  for (let month = 1; month <= months; month += 1) {
    const startingBalance = balance;
    const contribution = monthlyContribution;
    const preInterestBalance =
      input.contributionTiming === "beginning" ? startingBalance + contribution : startingBalance;

    const interest = preInterestBalance * monthlyReturnRate;
    const postInterestBalance = preInterestBalance + interest;
    const endingBalanceNominal =
      input.contributionTiming === "end" ? postInterestBalance + contribution : postInterestBalance;

    balance = endingBalanceNominal;

    const discountFactor = Math.pow(1 + monthlyInflationRate, month);
    const endingBalanceReal = input.inflationEnabled ? endingBalanceNominal / discountFactor : undefined;

    schedule.push({
      month,
      startingBalance,
      contribution,
      interest,
      endingBalanceNominal,
      endingBalanceReal,
      totalInvested: presentValue + monthlyContribution * month
    });
  }

  const growthFactor = Math.pow(1 + monthlyReturnRate, months);
  const annuityFactor = monthlyReturnRate === 0 ? months : (growthFactor - 1) / monthlyReturnRate;

  const futureValueNominal =
    monthlyReturnRate === 0
      ? presentValue + monthlyContribution * months
      : presentValue * growthFactor +
        monthlyContribution * annuityFactor * (input.contributionTiming === "beginning" ? 1 + monthlyReturnRate : 1);

  const totalInvested = presentValue + monthlyContribution * months;
  const totalNominalEarnings = futureValueNominal - totalInvested;

  const inflationFactor = Math.pow(1 + monthlyInflationRate, months);
  const futureValueReal = input.inflationEnabled ? futureValueNominal / inflationFactor : undefined;
  const purchasingPowerLoss = input.inflationEnabled ? futureValueNominal - (futureValueReal ?? 0) : undefined;

  const nominalReturnAccumulated = totalInvested === 0 ? 0 : futureValueNominal / totalInvested - 1;
  const totalRealEarnings = input.inflationEnabled ? (futureValueReal ?? 0) - totalInvested : undefined;
  const realReturnAccumulated =
    input.inflationEnabled && totalInvested !== 0 && futureValueReal !== undefined ? futureValueReal / totalInvested - 1 : undefined;

  return {
    months,
    monthlyReturnRate,
    monthlyInflationRate,
    futureValueNominal,
    futureValueReal,
    totalInvested,
    totalNominalEarnings,
    totalRealEarnings,
    purchasingPowerLoss,
    nominalReturnAccumulated,
    realReturnAccumulated,
    schedule
  };
};
