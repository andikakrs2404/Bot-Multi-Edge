'use client';

import { useEffect, useState, useMemo } from 'react';
import SymbolTable from '@/components/SymbolTable';
import SymbolDetailDrawer from '@/components/SymbolDetailDrawer';
import { getSymbols, SymbolRow } from '@/lib/api';

interface SymbolRegistryData {
  total: number;
  per_exchange: Record<string, number>;
  per_sector: Record<string, number>;
  symbols: SymbolRow[];
  classification_coverage: number;
}

export default function SymbolRegistry() {
  const [data, setData] = useState<SymbolRegistryData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const [search, setSearch] = useState('');
  const [filterExchange, setFilterExchange] = useState('');
  const [filterSector, setFilterSector] = useState('');
  const [selectedSymbol, setSelectedSymbol] = useState<string | null>(null);

  useEffect(() => {
    getSymbols()
      .then(setData)
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false));
  }, []);

  const filtered = useMemo(() => {
    if (!data) return [];
    let list = data.symbols;
    if (search) {
      const q = search.toLowerCase();
      list = list.filter((s) => s.symbol.toLowerCase().includes(q));
    }
    if (filterExchange) {
      list = list.filter((s) => s.exchange === filterExchange);
    }
    if (filterSector) {
      list = list.filter((s) => s.sector === filterSector);
    }
    return list;
  }, [data, search, filterExchange, filterSector]);

  // top unclassified (first 20 OTHER symbols)
  const unclassified = useMemo(() => {
    if (!data) return [];
    return data.symbols.filter((s) => s.sector === 'OTHER').slice(0, 20);
  }, [data]);

  if (loading) return <div className="text-center py-20 text-gray-400">Loading symbols…</div>;
  if (error) return <div className="text-center py-20 text-red-400">Failed to load: {error}</div>;
  if (!data) return null;

  const exchanges = Object.keys(data.per_exchange);
  const sectors = Object.keys(data.per_sector);
  const classified = data.total - (data.per_sector['OTHER'] || 0);
  const coveragePct = (data.classification_coverage * 100).toFixed(1);

  return (
    <div>
      <h1 className="text-2xl font-bold mb-4">Symbol Registry</h1>

      {/* Coverage Card */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
        <div className="rounded-lg border border-gray-700 bg-gray-900 p-4">
          <div className="text-gray-400 text-xs uppercase tracking-wide mb-1">Coverage</div>
          <div className="text-2xl font-bold" style={{ color: coveragePct === '0.0' ? '#ef4444' : '#22c55e' }}>
            {coveragePct}%
          </div>
          <div className="text-xs text-gray-500">{classified} / {data.total} classified</div>
        </div>
        <div className="rounded-lg border border-gray-700 bg-gray-900 p-4">
          <div className="text-gray-400 text-xs uppercase tracking-wide mb-1">Total Symbols</div>
          <div className="text-2xl font-bold text-white">{data.total}</div>
        </div>
        <div className="rounded-lg border border-gray-700 bg-gray-900 p-4">
          <div className="text-gray-400 text-xs uppercase tracking-wide mb-1">Exchanges</div>
          <div className="flex flex-wrap gap-2 mt-1">
            {Object.entries(data.per_exchange).map(([ex, count]) => (
              <span key={ex} className="text-sm">
                <span className="font-semibold text-white">{ex}</span>{' '}
                <span className="text-gray-400">({count})</span>
              </span>
            ))}
          </div>
        </div>
        <div className="rounded-lg border border-gray-700 bg-gray-900 p-4">
          <div className="text-gray-400 text-xs uppercase tracking-wide mb-1">Sectors</div>
          <div className="text-2xl font-bold text-white">{sectors.length}</div>
        </div>
      </div>

      {/* Sector Breakdown */}
      <div className="mb-6 rounded-lg border border-gray-700 bg-gray-900 p-4">
        <h2 className="text-sm font-semibold text-gray-300 mb-2">Sector Distribution</h2>
        <div className="flex flex-wrap gap-2">
          {Object.entries(data.per_sector)
            .sort(([, a], [, b]) => b - a)
            .map(([sec, count]) => {
              const pct = ((count / data.total) * 100).toFixed(1);
              return (
                <span key={sec} className="rounded bg-gray-800 px-2 py-1 text-xs">
                  <span className="font-medium text-white">{sec}</span>{' '}
                  <span className="text-gray-400">
                    {count} ({pct}%)
                  </span>
                </span>
              );
            })}
        </div>
      </div>

      {/* Search + Filters */}
      <div className="mb-4 flex flex-wrap gap-3">
        <input
          type="text"
          placeholder="Search symbol..."
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          className="rounded-md border border-gray-600 bg-gray-800 px-3 py-2 text-sm text-white placeholder-gray-500 focus:border-cyan-500 focus:outline-none"
          style={{ minWidth: 220 }}
        />
        <select
          value={filterExchange}
          onChange={(e) => setFilterExchange(e.target.value)}
          className="rounded-md border border-gray-600 bg-gray-800 px-3 py-2 text-sm text-white focus:border-cyan-500 focus:outline-none"
        >
          <option value="">All Exchanges</option>
          {exchanges.map((ex) => (
            <option key={ex} value={ex}>{ex}</option>
          ))}
        </select>
        <select
          value={filterSector}
          onChange={(e) => setFilterSector(e.target.value)}
          className="rounded-md border border-gray-600 bg-gray-800 px-3 py-2 text-sm text-white focus:border-cyan-500 focus:outline-none"
        >
          <option value="">All Sectors</option>
          {sectors.map((sec) => (
            <option key={sec} value={sec}>{sec}</option>
          ))}
        </select>
        <span className="self-center text-sm text-gray-500">
          {filtered.length} of {data.total}
        </span>
      </div>

      {/* UNKNOWN Review Queue */}
      {unclassified.length > 0 && !search && !filterExchange && !filterSector && (
        <div className="mb-4 rounded-lg border border-yellow-800 bg-yellow-900/20 p-3">
          <h3 className="text-sm font-semibold text-yellow-400 mb-2">
            Top Unclassified ({data.per_sector['OTHER'] || 0} symbols)
          </h3>
          <div className="flex flex-wrap gap-1.5">
            {unclassified.map((s) => (
              <button
                key={s.symbol}
                onClick={() => setSelectedSymbol(s.symbol)}
                className="rounded bg-gray-800 px-2 py-0.5 text-xs font-mono text-gray-300 hover:bg-gray-700 hover:text-white transition-colors"
              >
                {s.symbol}
              </button>
            ))}
            {(data.per_sector['OTHER'] || 0) > 20 && (
              <span className="text-xs text-gray-500 self-center">…and {(data.per_sector['OTHER'] || 0) - 20} more</span>
            )}
          </div>
        </div>
      )}

      {/* Table */}
      <SymbolTable data={filtered} onSelect={setSelectedSymbol} />

      {/* Detail Drawer */}
      {selectedSymbol && (
        <SymbolDetailDrawer
          symbol={selectedSymbol}
          onClose={() => setSelectedSymbol(null)}
        />
      )}
    </div>
  );
}
