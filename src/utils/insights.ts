import { format } from 'date-fns';
import { ptBR } from 'date-fns/locale';
import type { Entry, Insight } from '../types';

const pct = (current: number, previous: number) => ((current - previous) / previous) * 100;

export const buildInsights = (entries: Entry[]): Insight[] => {
  if (!entries.length) {
    return [{ title: 'Sem dados', description: 'Não há dados suficientes para gerar insights.', severity: 'warning' }];
  }

  const monthly = new Map<string, number>();
  const category = new Map<string, number>();

  entries.forEach((entry) => {
    monthly.set(entry.monthKey, (monthly.get(entry.monthKey) ?? 0) + entry.amount);
    category.set(entry.category, (category.get(entry.category) ?? 0) + entry.amount);
  });

  const monthList = [...monthly.entries()].sort(([a], [b]) => a.localeCompare(b));
  const highest = [...monthList].sort((a, b) => b[1] - a[1])[0];
  const lowest = [...monthList].sort((a, b) => a[1] - b[1])[0];
  const last2 = monthList.slice(-2);
  const insights: Insight[] = [];

  if (highest) {
    insights.push({
      title: 'Melhor mês de aporte',
      description: `${format(new Date(`${highest[0]}-01`), 'MMMM/yyyy', { locale: ptBR })} teve o maior aporte (R$ ${highest[1].toFixed(2)}).`,
      severity: 'success'
    });
  }

  if (lowest) {
    insights.push({
      title: 'Menor contribuição mensal',
      description: `${format(new Date(`${lowest[0]}-01`), 'MMMM/yyyy', { locale: ptBR })} foi o mês com menor valor aportado (R$ ${lowest[1].toFixed(2)}).`,
      severity: 'info'
    });
  }

  if (last2.length === 2 && last2[0][1] > 0) {
    const varPct = pct(last2[1][1], last2[0][1]);
    insights.push({
      title: 'Variação mensal recente',
      description: `O último mês variou ${varPct >= 0 ? '+' : ''}${varPct.toFixed(1)}% em relação ao mês anterior.`,
      severity: varPct < -15 ? 'warning' : 'info'
    });

    if (varPct < -15) {
      insights.push({
        title: 'Alerta de queda',
        description: 'Queda acentuada de aportes no último mês. Vale revisar o planejamento financeiro.',
        severity: 'warning'
      });
    }
  }

  const topCategory = [...category.entries()].sort((a, b) => b[1] - a[1])[0];
  const total = [...category.values()].reduce((acc, value) => acc + value, 0);

  if (topCategory && total > 0) {
    const concentration = (topCategory[1] / total) * 100;
    insights.push({
      title: 'Concentração por categoria',
      description: `${topCategory[0]} concentra ${concentration.toFixed(1)}% dos aportes totais.`,
      severity: concentration > 55 ? 'warning' : 'info'
    });
  }

  const streak = monthList.every((item, idx, arr) => idx === 0 || item[1] >= arr[idx - 1][1]);
  insights.push({
    title: 'Consistência de aportes',
    description: streak
      ? 'Os aportes mensais mantiveram tendência de crescimento consistente.'
      : 'Os aportes variaram ao longo do tempo, com sinais de inconsistência.',
    severity: streak ? 'success' : 'info'
  });

  return insights;
};
