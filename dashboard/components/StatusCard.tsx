export default function StatusCard({ exchange }: { exchange: { exchange: string; is_connected: boolean; uptime_seconds: number; reconnect_count: number } }) {
  const fmt = (s: number) => {
    const h = Math.floor(s / 3600);
    const m = Math.floor((s % 3600) / 60);
    return `${h}h ${m}m`;
  };

  return (
    <div className="rounded-lg border border-gray-700 bg-gray-900 p-5">
      <div className="flex items-center justify-between mb-3">
        <h3 className="text-lg font-semibold text-white">{exchange.exchange}</h3>
        <span
          className={`h-3 w-3 rounded-full ${
            exchange.is_connected ? 'bg-green-500 shadow-[0_0_8px_#22c55e]' : 'bg-red-500 shadow-[0_0_8px_#ef4444]'
          }`}
        />
      </div>
      <dl className="space-y-1 text-sm">
        <div className="flex justify-between">
          <dt className="text-gray-400">Uptime</dt>
          <dd className="text-gray-100">{fmt(exchange.uptime_seconds)}</dd>
        </div>
        <div className="flex justify-between">
          <dt className="text-gray-400">Reconnects</dt>
          <dd className="text-gray-100">{exchange.reconnect_count}</dd>
        </div>
      </dl>
    </div>
  );
}
