import * as XLSX from 'xlsx';
import { format, parse, parseISO } from 'date-fns';
import type { ColumnMapping, DashboardData, Entry, RawRow } from '../types';
import { buildInsights } from '../utils/insights';

const SAMPLE_ROWS: RawRow[] = [
  { Data: '2025-01-15', Aporte: 1500, Categoria: 'Renda Fixa', Ativo: 'Tesouro Selic', Patrimonio: 12000, Rendimento: 110 },
  { Data: '2025-02-15', Aporte: 1600, Categoria: 'Ações', Ativo: 'ETF BOVA11', Patrimonio: 14050, Rendimento: 190 },
  { Data: '2025-03-15', Aporte: 1800, Categoria: 'Fundos', Ativo: 'FII MXRF11', Patrimonio: 16220, Rendimento: 210 },
  { Data: '2025-04-15', Aporte: 1200, Categoria: 'Ações', Ativo: 'PETR4', Patrimonio: 17580, Rendimento: -90 },
  { Data: '2025-05-15', Aporte: 2000, Categoria: 'Renda Fixa', Ativo: 'CDB Banco X', Patrimonio: 20100, Rendimento: 260 }
];

const normalize = (input: string) =>
  input
    .toLowerCase()
    .normalize('NFD')
    .replace(/[\u0300-\u036f]/g, '')
    .trim();

const parseNumber = (value: unknown): number | undefined => {
  if (typeof value === 'number') return Number.isFinite(value) ? value : undefined;
  if (typeof value !== 'string') return undefined;
  const cleaned = value.replace(/\./g, '').replace(',', '.').replace(/[^0-9.-]/g, '');
  const parsed = Number(cleaned);
  return Number.isFinite(parsed) ? parsed : undefined;
};

const parseDateLike = (value: unknown): Date | undefined => {
  if (value instanceof Date && !Number.isNaN(value.getTime())) return value;

  if (typeof value === 'number') {
    const parsed = XLSX.SSF.parse_date_code(value);
    if (!parsed) return undefined;
    return new Date(parsed.y, parsed.m - 1, parsed.d);
  }

  if (typeof value !== 'string') return undefined;
  const candidate = value.trim();
  if (!candidate) return undefined;

  const iso = parseISO(candidate);
  if (!Number.isNaN(iso.getTime())) return iso;

  const ptBr = parse(candidate, 'dd/MM/yyyy', new Date());
  if (!Number.isNaN(ptBr.getTime())) return ptBr;

  const monthYear = parse(candidate, 'MM/yyyy', new Date());
  if (!Number.isNaN(monthYear.getTime())) return monthYear;

  return undefined;
};

export const inferMapping = (headers: string[]): ColumnMapping => {
  const mapped: ColumnMapping = {};

  headers.forEach((header) => {
    const n = normalize(header);
    if (!mapped.date && (n.includes('data') || n.includes('dt'))) mapped.date = header;
    if (!mapped.monthYear && (n.includes('mes') || n.includes('competencia') || n.includes('periodo') || n.includes('ano'))) mapped.monthYear = header;
    if (!mapped.amount && (n.includes('aporte') || n.includes('valor') || n.includes('aplicacao'))) mapped.amount = header;
    if (!mapped.category && n.includes('categoria')) mapped.category = header;
    if (!mapped.investment && (n.includes('ativo') || n.includes('invest') || n.includes('produto'))) mapped.investment = header;
    if (!mapped.patrimony && (n.includes('patrimonio') || n.includes('saldo') || n.includes('carteira'))) mapped.patrimony = header;
    if (!mapped.yield && (n.includes('rendimento') || n.includes('rentabilidade') || n.includes('lucro'))) mapped.yield = header;
  });

  return mapped;
};

export const rowsToEntries = (rows: RawRow[], mapping: ColumnMapping): DashboardData => {
  const errors: string[] = [];
  const entries: Entry[] = [];

  rows.forEach((row, idx) => {
    const amount = parseNumber(mapping.amount ? row[mapping.amount] : undefined);
    const date = parseDateLike(mapping.date ? row[mapping.date] : mapping.monthYear ? row[mapping.monthYear] : undefined);

    if (!amount || !date) {
      errors.push(`Linha ${idx + 2}: ignorada por falta de data ou valor de aporte válido.`);
      return;
    }

    const patrimony = parseNumber(mapping.patrimony ? row[mapping.patrimony] : undefined);
    const yieldValue = parseNumber(mapping.yield ? row[mapping.yield] : undefined);

    entries.push({
      amount,
      date,
      monthKey: format(date, 'yyyy-MM'),
      category: String(mapping.category ? row[mapping.category] ?? 'Sem categoria' : 'Sem categoria'),
      investment: String(mapping.investment ? row[mapping.investment] ?? 'Não informado' : 'Não informado'),
      patrimony,
      yield: yieldValue
    });
  });

  entries.sort((a, b) => a.date.getTime() - b.date.getTime());
  return { entries, errors, insights: buildInsights(entries) };
};

const parseWorkbook = (arrayBuffer: ArrayBuffer) => {
  const workbook = XLSX.read(arrayBuffer, { type: 'array' });
  const firstSheetName = workbook.SheetNames[0];
  if (!firstSheetName) return [] as RawRow[];
  const sheet = workbook.Sheets[firstSheetName];
  return XLSX.utils.sheet_to_json<RawRow>(sheet, { defval: null });
};

export const loadDefaultSpreadsheet = async (): Promise<{ rows: RawRow[]; source: string }> => {
  try {
    const response = await fetch('/planilha%20de%20aportes.xlsx');
    if (!response.ok) throw new Error('Arquivo padrão não encontrado no diretório public.');
    const rows = parseWorkbook(await response.arrayBuffer());
    return { rows, source: 'planilha de aportes.xlsx' };
  } catch {
    return { rows: SAMPLE_ROWS, source: 'dados de exemplo (fallback)' };
  }
};

export const parseUploadedFile = async (file: File): Promise<RawRow[]> => {
  const buffer = await file.arrayBuffer();
  return parseWorkbook(buffer);
};
