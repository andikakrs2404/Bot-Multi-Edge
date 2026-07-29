const BASE = 'http://localhost:8000/api';

async function fetcher<T>(path: string): Promise<T> {
  const res = await fetch(`${BASE}${path}`);
  if (!res.ok) {
    const body = await res.text().catch(() => '');
    throw new Error(`GET ${path} ${res.status}${body ? `: ${body}` : ''}`);
  }
  return res.json();
}

export interface ExchangeInfo {
  exchange: string;
  is_connected: boolean;
  uptime_seconds: number;
  reconnect_count: number;
}

export function getSystemStatus() {
  return fetcher<{ exchanges: ExchangeInfo[]; health_score: number; total_symbols: number }>('/system/status');
}

export interface SymbolRow {
  symbol: string;
  exchange: string;
  sector: string;
  tags: string[];
  status: string;
}

export interface SymbolListResponse {
  total: number;
  per_exchange: Record<string, number>;
  per_sector: Record<string, number>;
  symbols: SymbolRow[];
  classification_coverage: number;
}

export function getSymbols(): Promise<SymbolListResponse> {
  return fetcher<SymbolListResponse>('/symbols');
}

export function getSymbol(symbol: string) {
  return fetcher<{ symbol: string; exchange: string; sector: string; tags: string[]; listing_age_days: number; status: string }>(`/symbols/${encodeURIComponent(symbol)}`);
}
