"use client";

import { useMemo, useState } from "react";
import { calculateFutureValue, type CalculatorInput, type InflationIndex } from "@/src/lib/futureValue";

const INFLATION_DEFAULTS: Record<InflationIndex, number> = {
  ipca: 4.5,
  igpm: 5.5,
  manual: 4
};

const currencyBRL = new Intl.NumberFormat("pt-BR", { style: "currency", currency: "BRL" });
const percentBR = new Intl.NumberFormat("pt-BR", { maximumFractionDigits: 2, minimumFractionDigits: 2 });

export default function Page() {
  const [input, setInput] = useState<CalculatorInput>({
    presentValue: 0,
    monthlyContribution: 1000,
    returnRatePercent: 10,
    returnRatePeriod: "annual",
    termValue: 10,
    termUnit: "years",
    contributionTiming: "end",
    inflationEnabled: true,
    inflationType: "ipca",
    inflationAnnualPercent: INFLATION_DEFAULTS.ipca
  });

  const result = useMemo(() => calculateFutureValue(input), [input]);

  const handleNumber = (field: keyof CalculatorInput, value: string) => {
    setInput((prev) => ({ ...prev, [field]: value === "" ? undefined : Number(value) }));
  };

  const points = result.schedule;
  const maxY = Math.max(...points.map((p) => p.endingBalanceNominal), result.totalInvested, 1);

  return (
    <main className="mx-auto max-w-7xl p-6 space-y-6">
      <h1 className="text-3xl font-bold">Calculadora dinâmica de Future Value</h1>

      <section className="grid gap-4 md:grid-cols-2 lg:grid-cols-3 card">
        <Input label="Valor inicial investido, PV" type="number" value={input.presentValue ?? ""} onChange={(v) => handleNumber("presentValue", v)} />
        <Input label="Aporte mensal" type="number" value={input.monthlyContribution ?? ""} onChange={(v) => handleNumber("monthlyContribution", v)} />
        <Input label="Taxa de retorno (%)" type="number" value={input.returnRatePercent ?? ""} onChange={(v) => handleNumber("returnRatePercent", v)} />

        <Select label="Periodicidade da taxa" value={input.returnRatePeriod} onChange={(v) => setInput((p) => ({ ...p, returnRatePeriod: v as "monthly" | "annual" }))} options={[{ label: "Mensal", value: "monthly" }, { label: "Anual", value: "annual" }]} />
        <Input label="Prazo" type="number" min={0} value={input.termValue ?? ""} onChange={(v) => handleNumber("termValue", v)} />
        <Select label="Unidade do prazo" value={input.termUnit} onChange={(v) => setInput((p) => ({ ...p, termUnit: v as "months" | "years" }))} options={[{ label: "Meses", value: "months" }, { label: "Anos", value: "years" }]} />

        <Select label="Tipo de aporte" value={input.contributionTiming} onChange={(v) => setInput((p) => ({ ...p, contributionTiming: v as "beginning" | "end" }))} options={[{ label: "No início do mês", value: "beginning" }, { label: "No final do mês", value: "end" }]} />
      </section>

      <section className="card space-y-4">
        <label className="flex items-center gap-2"><input type="checkbox" checked={input.inflationEnabled} onChange={(e) => setInput((p) => ({ ...p, inflationEnabled: e.target.checked }))} /> Ajustar por inflação</label>
        {input.inflationEnabled && (
          <div className="grid gap-4 md:grid-cols-3">
            <Select label="Índice" value={input.inflationType} onChange={(v) => setInput((p) => ({ ...p, inflationType: v as InflationIndex, inflationAnnualPercent: INFLATION_DEFAULTS[v as InflationIndex] }))} options={[{ label: "IPCA", value: "ipca" }, { label: "IGP-M", value: "igpm" }, { label: "Taxa manual", value: "manual" }]} />
            <Input label="Inflação anual (%)" type="number" value={input.inflationAnnualPercent ?? ""} onChange={(v) => handleNumber("inflationAnnualPercent", v)} />
          </div>
        )}
      </section>

      <section className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
        <Card title="Valor futuro nominal" value={currencyBRL.format(result.futureValueNominal)} highlight />
        {input.inflationEnabled && <Card title="Valor futuro real" value={currencyBRL.format(result.futureValueReal ?? 0)} highlight />}
        <Card title="Total investido" value={currencyBRL.format(result.totalInvested)} />
        <Card title="Rendimento acumulado nominal" value={currencyBRL.format(result.totalNominalEarnings)} />
        {input.inflationEnabled && <Card title="Rendimento real" value={currencyBRL.format(result.totalRealEarnings ?? 0)} />}
        <Card title="Taxa mensal equivalente" value={`${percentBR.format(result.monthlyReturnRate * 100)}%`} />
        {input.inflationEnabled && <Card title="Inflação mensal equivalente" value={`${percentBR.format(result.monthlyInflationRate * 100)}%`} />}
        {input.inflationEnabled && <Card title="Perda de poder de compra" value={currencyBRL.format(result.purchasingPowerLoss ?? 0)} />}
        <Card title="Rentabilidade nominal acumulada" value={`${percentBR.format(result.nominalReturnAccumulated * 100)}%`} />
        {input.inflationEnabled && <Card title="Rentabilidade real acumulada" value={`${percentBR.format((result.realReturnAccumulated ?? 0) * 100)}%`} />}
      </section>

      <section className="card">
        <h2 className="font-semibold mb-3">Evolução mensal</h2>
        <svg viewBox="0 0 800 280" className="w-full h-72 bg-slate-50 rounded">
          {points.length > 0 && (
            <>
              <polyline fill="none" stroke="#2563eb" strokeWidth="2" points={points.map((p, i) => `${(i / Math.max(points.length - 1, 1)) * 760 + 20},${250 - (p.endingBalanceNominal / maxY) * 220}`).join(" ")} />
              <polyline fill="none" stroke="#16a34a" strokeWidth="2" points={points.map((p, i) => `${(i / Math.max(points.length - 1, 1)) * 760 + 20},${250 - (p.totalInvested / maxY) * 220}`).join(" ")} />
              {input.inflationEnabled && <polyline fill="none" stroke="#dc2626" strokeWidth="2" points={points.map((p, i) => `${(i / Math.max(points.length - 1, 1)) * 760 + 20},${250 - ((p.endingBalanceReal ?? 0) / maxY) * 220}`).join(" ")} />}
            </>
          )}
        </svg>
      </section>

      <section className="card overflow-auto">
        <table className="w-full text-sm">
          <thead><tr className="text-left border-b"><th>Mês</th><th>Saldo inicial</th><th>Aporte</th><th>Juros</th><th>Saldo final nominal</th>{input.inflationEnabled && <th>Saldo real ajustado</th>}</tr></thead>
          <tbody>
            {result.schedule.map((row) => (
              <tr key={row.month} className="border-b last:border-none">
                <td>{row.month}</td><td>{currencyBRL.format(row.startingBalance)}</td><td>{currencyBRL.format(row.contribution)}</td><td>{currencyBRL.format(row.interest)}</td><td>{currencyBRL.format(row.endingBalanceNominal)}</td>{input.inflationEnabled && <td>{currencyBRL.format(row.endingBalanceReal ?? 0)}</td>}
              </tr>
            ))}
          </tbody>
        </table>
      </section>
    </main>
  );
}

function Input({ label, ...props }: any) {
  return <label className="flex flex-col gap-1 text-sm"><span>{label}</span><input className="rounded border p-2" {...props} /></label>;
}
function Select({ label, options, ...props }: any) {
  return <label className="flex flex-col gap-1 text-sm"><span>{label}</span><select className="rounded border p-2" {...props}>{options.map((o: any) => <option key={o.value} value={o.value}>{o.label}</option>)}</select></label>;
}
function Card({ title, value, highlight = false }: { title: string; value: string; highlight?: boolean }) {
  return <div className={`card ${highlight ? "border-blue-400" : ""}`}><p className="text-slate-500 text-sm">{title}</p><p className="text-xl font-semibold">{value}</p></div>;
}
