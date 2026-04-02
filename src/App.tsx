import { useEffect, useMemo, useState } from 'react';
import { format } from 'date-fns';
import { ptBR } from 'date-fns/locale';
import { ChartsPanel } from './components/ChartsPanel';
import { InsightsList } from './components/InsightsList';
import { KpiCard } from './components/KpiCard';
import { MappingEditor } from './components/MappingEditor';
import { inferMapping, loadDefaultSpreadsheet, parseUploadedFile, rowsToEntries } from './services/spreadsheet';
import type { ColumnMapping, DashboardData, RawRow } from './types';

const currency = (value: number) => new Intl.NumberFormat('pt-BR', { style: 'currency', currency: 'BRL' }).format(value);

function App() {
  const [rows, setRows] = useState<RawRow[]>([]);
  const [source, setSource] = useState('');
  const [mapping, setMapping] = useState<ColumnMapping>({});
  const [data, setData] = useState<DashboardData>({ entries: [], insights: [], errors: [] });

  const headers = useMemo(() => (rows[0] ? Object.keys(rows[0]) : []), [rows]);

  useEffect(() => {
    loadDefaultSpreadsheet().then(({ rows: loadedRows, source: loadedSource }) => {
      setRows(loadedRows);
      setSource(loadedSource);
      setMapping(inferMapping(Object.keys(loadedRows[0] ?? {})));
    });
  }, []);

  useEffect(() => {
    if (!rows.length || !mapping.amount || (!mapping.date && !mapping.monthYear)) return;
    setData(rowsToEntries(rows, mapping));
  }, [rows, mapping]);

  const monthlyData = useMemo(() => {
    const monthlyMap = new Map<string, number>();
    data.entries.forEach((entry) => {
      monthlyMap.set(entry.monthKey, (monthlyMap.get(entry.monthKey) ?? 0) + entry.amount);
    });

    let accumulated = 0;
    return [...monthlyMap.entries()]
      .sort(([a], [b]) => a.localeCompare(b))
      .map(([month, aporte]) => {
        accumulated += aporte;
        return { month, aporte, acumulado: accumulated };
      });
  }, [data.entries]);

  const categoryData = useMemo(() => {
    const map = new Map<string, number>();
    data.entries.forEach((entry) => {
      map.set(entry.category, (map.get(entry.category) ?? 0) + entry.amount);
    });
    return [...map.entries()].map(([categoria, valor]) => ({ categoria, valor }));
  }, [data.entries]);

  const kpis = useMemo(() => {
    if (!data.entries.length) return null;

    const nowMonth = format(new Date(), 'yyyy-MM');
    const nowYear = format(new Date(), 'yyyy');
    const totalMonth = data.entries.filter((entry) => entry.monthKey === nowMonth).reduce((acc, value) => acc + value.amount, 0);
    const totalYear = data.entries.filter((entry) => entry.monthKey.startsWith(nowYear)).reduce((acc, value) => acc + value.amount, 0);
    const total = data.entries.reduce((acc, value) => acc + value.amount, 0);
    const avg = total / monthlyData.length;
    const max = Math.max(...data.entries.map((entry) => entry.amount));
    const min = Math.min(...data.entries.map((entry) => entry.amount));
    const patrimony = data.entries
      .map((entry) => entry.patrimony)
      .filter((value): value is number => typeof value === 'number')
      .at(-1);

    const growth =
      monthlyData.length > 1 && monthlyData[monthlyData.length - 2].aporte > 0
        ? ((monthlyData[monthlyData.length - 1].aporte - monthlyData[monthlyData.length - 2].aporte) /
            monthlyData[monthlyData.length - 2].aporte) *
          100
        : 0;

    return { totalMonth, totalYear, avg, max, min, growth, patrimony, total };
  }, [data.entries, monthlyData]);

  const handleUpload = async (file?: File) => {
    if (!file) return;
    const parsedRows = await parseUploadedFile(file);
    setRows(parsedRows);
    setSource(file.name);
    setMapping(inferMapping(Object.keys(parsedRows[0] ?? {})));
  };

  return (
    <main className="container">
      <header>
        <h1>Dashboard de Aportes Mensais</h1>
        <p>Fonte atual: {source || 'carregando...'}</p>
        <div className="uploader">
          <label>
            Trocar planilha (.xlsx)
            <input type="file" accept=".xlsx,.xls" onChange={(e) => handleUpload(e.target.files?.[0])} />
          </label>
        </div>
      </header>

      <MappingEditor headers={headers} mapping={mapping} onChange={setMapping} />

      {kpis ? (
        <>
          <section className="kpi-grid">
            <KpiCard title="Total aportado no mês atual" value={currency(kpis.totalMonth)} />
            <KpiCard title="Total aportado no ano atual" value={currency(kpis.totalYear)} />
            <KpiCard title="Média mensal de aportes" value={currency(kpis.avg)} />
            <KpiCard title="Maior aporte" value={currency(kpis.max)} />
            <KpiCard title="Menor aporte" value={currency(kpis.min)} />
            <KpiCard title="Crescimento mês a mês" value={`${kpis.growth.toFixed(1)}%`} />
            <KpiCard title="Evolução acumulada" value={currency(kpis.total)} />
            <KpiCard title="Patrimônio total" value={kpis.patrimony ? currency(kpis.patrimony) : 'Não informado'} />
          </section>

          <ChartsPanel monthly={monthlyData} categories={categoryData} />
          <InsightsList insights={data.insights} />
        </>
      ) : (
        <div className="card">
          <h2>Dados insuficientes</h2>
          <p>Confirme o mapeamento das colunas de data/mês e valor do aporte.</p>
        </div>
      )}

      {data.errors.length > 0 && (
        <div className="card errors">
          <h2>Alertas de importação</h2>
          <ul>
            {data.errors.map((error) => (
              <li key={error}>{error}</li>
            ))}
          </ul>
        </div>
      )}

      <footer>
        <small>
          Última atualização: {format(new Date(), "dd 'de' MMMM 'de' yyyy", { locale: ptBR })}
        </small>
      </footer>
    </main>
  );
}

export default App;
