'use client';

import { useEffect, useState } from 'react';
import { getSymbol } from '@/lib/api';

export default function SymbolDetailDrawer({
  symbol,
  onClose,
}: {
  symbol: string;
  onClose: () => void;
}) {
  const [detail, setDetail] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    setLoading(true);
    setError(null);
    getSymbol(symbol)
      .then(setDetail)
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false));
  }, [symbol]);

  const rows: [string, string | number][] = detail
    ? [
        ['Symbol', detail.symbol],
        ['Exchange', detail.exchange],
        ['Sector', detail.sector],
        ['Tags', (detail.tags as string[]).join(', ') || '—'],
        ['Listing Age', `${detail.listing_age_days} days`],
        ['Status', detail.status],
      ]
    : [];

  return (
    <>
      {/* backdrop */}
      <div
        className="fixed inset-0 z-40 bg-black/50"
        onClick={onClose}
      />

      {/* drawer */}
      <div className="fixed right-0 top-0 z-50 h-full w-96 border-l border-gray-700 bg-gray-900 shadow-2xl overflow-y-auto">
        <div className="flex items-center justify-between border-b border-gray-700 px-4 py-3">
          <h2 className="text-lg font-bold text-white">Symbol Detail</h2>
          <button
            onClick={onClose}
            className="rounded p-1 text-gray-400 hover:bg-gray-800 hover:text-white transition-colors"
          >
            <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <line x1="18" y1="6" x2="6" y2="18" /><line x1="6" y1="6" x2="18" y2="18" />
            </svg>
          </button>
        </div>

        <div className="p-4">
          {loading && <div className="text-gray-400 text-sm">Loading…</div>}
          {error && <div className="text-red-400 text-sm">Error: {error}</div>}
          {detail && (
            <div className="space-y-3">
              {rows.map(([label, value]) => (
                <div key={label}>
                  <div className="text-xs text-gray-500 uppercase tracking-wide">{label}</div>
                  <div className="text-sm font-medium text-white mt-0.5">{value}</div>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* placeholder for future Feature Store panels */}
        <div className="border-t border-gray-700 px-4 py-3">
          <div className="text-xs text-gray-500 uppercase tracking-wide mb-2">Feature Store</div>
          <div className="space-y-1">
            {['Raw Features', 'Normalized Features', 'Breadth', 'Attention', 'Tier', 'Opportunity', 'Edge'].map(
              (label) => (
                <div
                  key={label}
                  className="rounded bg-gray-800 px-2 py-1.5 text-xs text-gray-500 italic"
                >
                  {label} — coming in ADR-004+
                </div>
              )
            )}
          </div>
        </div>
      </div>
    </>
  );
}
