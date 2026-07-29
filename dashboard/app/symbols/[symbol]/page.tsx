'use client';

import { useEffect, useState } from 'react';
import { useParams } from 'next/navigation';

interface SymbolDetail {
  symbol: string;
  exchange: string;
  sector: string;
  tags: string[];
  listing_age_days: number;
  status: string;
}

export default function SymbolDetailPage() {
  const { symbol } = useParams<{ symbol: string }>();
  const [detail, setDetail] = useState<SymbolDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetch(`http://localhost:8000/api/symbols/${symbol}`)
      .then((r) => {
        if (!r.ok) throw new Error(`HTTP ${r.status}`);
        return r.json();
      })
      .then((d) => {
        setDetail(d);
        setLoading(false);
      })
      .catch((e) => {
        setError(e.message);
        setLoading(false);
      });
  }, [symbol]);

  if (loading) return <div className="text-center py-20 text-gray-400">Loading symbol…</div>;
  if (error) return <div className="text-center py-20 text-red-400">Failed to load: {error}</div>;
  if (!detail) return null;

  const rows: [string, string | number][] = [
    ['Symbol', detail.symbol],
    ['Exchange', detail.exchange],
    ['Sector', detail.sector],
    ['Tags', detail.tags.join(', ')],
    ['Listing Age (days)', detail.listing_age_days],
    ['Status', detail.status],
  ];

  return (
    <div>
      <h1 className="text-2xl font-bold mb-6 font-mono text-cyan-400">{detail.symbol}</h1>

      <div className="rounded-lg border border-gray-700 bg-gray-900">
        <dl className="divide-y divide-gray-700">
          {rows.map(([label, value]) => (
            <div key={label} className="flex px-6 py-4">
              <dt className="w-48 text-sm font-medium text-gray-400">{label}</dt>
              <dd className="text-sm text-gray-100">{value}</dd>
            </div>
          ))}
        </dl>
      </div>
    </div>
  );
}
