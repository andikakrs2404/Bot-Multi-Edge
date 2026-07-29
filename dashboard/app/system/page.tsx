'use client';

import { useEffect, useState } from 'react';
import StatusCard from '@/components/StatusCard';
import useWebSocket from '@/hooks/useWebSocket';

interface ExchangeStatus {
  exchange: string;
  is_connected: boolean;
  uptime_seconds: number;
  reconnect_count: number;
}

interface SystemStatus {
  exchanges: ExchangeStatus[];
  health_score: number;
  total_symbols: number;
}

export default function SystemOverview() {
  const [status, setStatus] = useState<SystemStatus | null>(null);
  const [coverage, setCoverage] = useState<number | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    Promise.all([
      fetch('http://localhost:8000/api/system/status').then((r) => r.json()),
      fetch('http://localhost:8000/api/symbols').then((r) => r.json()),
    ])
      .then(([sys, sym]) => {
        setStatus(sys);
        setCoverage(sym.classification_coverage ?? null);
        setLoading(false);
      })
      .catch((e) => {
        setError(e.message);
        setLoading(false);
      });
  }, []);

  useWebSocket('ws://localhost:8000/ws/status', (msg) => {
    if (msg.type === 'status_update' && msg.data) {
      setStatus(msg.data);
    }
  });

  if (loading) return <div className="text-center py-20 text-gray-400">Loading system status…</div>;
  if (error) return <div className="text-center py-20 text-red-400">Failed to load: {error}</div>;
  if (!status) return null;

  return (
    <div>
      <h1 className="text-2xl font-bold mb-6">System Overview</h1>

      <div className="mb-6">
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
          <div className="rounded-lg border border-gray-700 bg-gray-900 p-4">
            <span className="text-sm text-gray-400">Total Symbols</span>
            <div className="text-3xl font-bold text-white">{status.total_symbols}</div>
          </div>
          <div className="rounded-lg border border-gray-700 bg-gray-900 p-4">
            <span className="text-sm text-gray-400">Health Score</span>
            <div className={`text-3xl font-bold ${status.health_score >= 80 ? 'text-green-400' : status.health_score >= 40 ? 'text-yellow-400' : 'text-red-400'}`}>
              {status.health_score.toFixed(0)}
            </div>
          </div>
          <div className="rounded-lg border border-gray-700 bg-gray-900 p-4">
            <span className="text-sm text-gray-400">Classification Coverage</span>
            <div className={`text-3xl font-bold ${coverage !== null && coverage >= 0.8 ? 'text-green-400' : coverage !== null && coverage >= 0.4 ? 'text-yellow-400' : 'text-yellow-400'}`}>
              {coverage !== null ? `${(coverage * 100).toFixed(1)}%` : '—'}
            </div>
          </div>
          <div className="rounded-lg border border-gray-700 bg-gray-900 p-4">
            <span className="text-sm text-gray-400">Exchanges</span>
            <div className="text-3xl font-bold text-white">{status.exchanges.length}</div>
          </div>
        </div>
      </div>

      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
        {status.exchanges.map((ex: any) => (
          <StatusCard key={ex.exchange} exchange={ex} />
        ))}
      </div>
    </div>
  );
}
