export type RawRow = Record<string, string | number | Date | null | undefined>;

export type ColumnMapping = {
  date?: string;
  monthYear?: string;
  amount?: string;
  category?: string;
  investment?: string;
  patrimony?: string;
  yield?: string;
};

export type Entry = {
  date: Date;
  monthKey: string;
  amount: number;
  category: string;
  investment: string;
  patrimony?: number;
  yield?: number;
};

export type Insight = {
  title: string;
  description: string;
  severity: 'info' | 'warning' | 'success';
};

export type DashboardData = {
  entries: Entry[];
  insights: Insight[];
  errors: string[];
};
