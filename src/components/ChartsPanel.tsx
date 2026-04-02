import { format } from 'date-fns';
import { ptBR } from 'date-fns/locale';
import {
  Bar,
  BarChart,
  CartesianGrid,
  Legend,
  Line,
  LineChart,
  Pie,
  PieChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
  Cell
} from 'recharts';

type MonthlyRow = { month: string; aporte: number; acumulado: number };
type CategoryRow = { categoria: string; valor: number };

const colors = ['#3b82f6', '#10b981', '#f59e0b', '#f43f5e', '#6366f1', '#14b8a6'];

const money = (value: number) =>
  new Intl.NumberFormat('pt-BR', { style: 'currency', currency: 'BRL', maximumFractionDigits: 0 }).format(value);

export function ChartsPanel({ monthly, categories }: { monthly: MonthlyRow[]; categories: CategoryRow[] }) {
  return (
    <div className="charts-grid">
      <div className="card chart-card">
        <h2>Aportes por mês</h2>
        <ResponsiveContainer width="100%" height={260}>
          <BarChart data={monthly}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey="month" tickFormatter={(m) => format(new Date(`${m}-01`), 'MM/yy', { locale: ptBR })} />
            <YAxis tickFormatter={money} />
            <Tooltip formatter={(v: number) => money(v)} />
            <Bar dataKey="aporte" fill="#2563eb" radius={[8, 8, 0, 0]} />
          </BarChart>
        </ResponsiveContainer>
      </div>

      <div className="card chart-card">
        <h2>Evolução acumulada</h2>
        <ResponsiveContainer width="100%" height={260}>
          <LineChart data={monthly}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey="month" tickFormatter={(m) => format(new Date(`${m}-01`), 'MM/yy', { locale: ptBR })} />
            <YAxis tickFormatter={money} />
            <Tooltip formatter={(v: number) => money(v)} />
            <Line type="monotone" dataKey="acumulado" stroke="#10b981" strokeWidth={3} />
          </LineChart>
        </ResponsiveContainer>
      </div>

      <div className="card chart-card">
        <h2>Divisão por categoria</h2>
        <ResponsiveContainer width="100%" height={260}>
          <PieChart>
            <Pie data={categories} dataKey="valor" nameKey="categoria" outerRadius={95} label>
              {categories.map((entry, idx) => (
                <Cell key={entry.categoria} fill={colors[idx % colors.length]} />
              ))}
            </Pie>
            <Tooltip formatter={(v: number) => money(v)} />
            <Legend />
          </PieChart>
        </ResponsiveContainer>
      </div>

      <div className="card chart-card">
        <h2>Comparação e tendência</h2>
        <ResponsiveContainer width="100%" height={260}>
          <LineChart data={monthly}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey="month" tickFormatter={(m) => format(new Date(`${m}-01`), 'MM/yy', { locale: ptBR })} />
            <YAxis tickFormatter={money} />
            <Tooltip formatter={(v: number) => money(v)} />
            <Legend />
            <Line type="monotone" dataKey="aporte" stroke="#f59e0b" strokeWidth={2} name="Aporte mensal" />
            <Line type="monotone" dataKey="acumulado" stroke="#6366f1" strokeWidth={2} name="Linha de tendência" />
          </LineChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}
