import type { ColumnMapping } from '../types';

const fields: Array<{ key: keyof ColumnMapping; label: string }> = [
  { key: 'date', label: 'Data' },
  { key: 'monthYear', label: 'Mês/Ano' },
  { key: 'amount', label: 'Valor do aporte' },
  { key: 'category', label: 'Categoria' },
  { key: 'investment', label: 'Ativo / Investimento' },
  { key: 'patrimony', label: 'Saldo / Patrimônio' },
  { key: 'yield', label: 'Rendimento' }
];

export function MappingEditor({
  headers,
  mapping,
  onChange
}: {
  headers: string[];
  mapping: ColumnMapping;
  onChange: (next: ColumnMapping) => void;
}) {
  return (
    <div className="card">
      <h2>Mapeamento de colunas</h2>
      <p className="subtitle">Ajuste se a inferência automática não estiver correta.</p>
      <div className="mapping-grid">
        {fields.map((field) => (
          <label key={field.key}>
            {field.label}
            <select
              value={mapping[field.key] ?? ''}
              onChange={(event) => onChange({ ...mapping, [field.key]: event.target.value || undefined })}
            >
              <option value="">Não mapear</option>
              {headers.map((header) => (
                <option key={header} value={header}>
                  {header}
                </option>
              ))}
            </select>
          </label>
        ))}
      </div>
    </div>
  );
}
