import type { ReactNode } from 'react';

type Props = {
  title: string;
  value: string;
  helper?: string;
  icon?: ReactNode;
};

export function KpiCard({ title, value, helper, icon }: Props) {
  return (
    <div className="card kpi-card">
      <div className="kpi-header">
        <h3>{title}</h3>
        <span>{icon}</span>
      </div>
      <strong>{value}</strong>
      {helper && <small>{helper}</small>}
    </div>
  );
}
