import type { Insight } from '../types';

const severityLabel: Record<Insight['severity'], string> = {
  info: 'info',
  success: 'sucesso',
  warning: 'atenção'
};

export function InsightsList({ insights }: { insights: Insight[] }) {
  return (
    <div className="card">
      <h2>Insights automáticos</h2>
      <ul className="insights-list">
        {insights.map((insight) => (
          <li key={insight.title} className={`insight ${insight.severity}`}>
            <div>
              <strong>{insight.title}</strong>
              <p>{insight.description}</p>
            </div>
            <span>{severityLabel[insight.severity]}</span>
          </li>
        ))}
      </ul>
    </div>
  );
}
