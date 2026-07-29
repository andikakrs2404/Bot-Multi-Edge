import {
  useReactTable,
  getCoreRowModel,
  flexRender,
  createColumnHelper,
} from '@tanstack/react-table';

interface SymbolRow {
  symbol: string;
  exchange: string;
  sector: string;
  tags: string[];
  status: string;
}

const helper = createColumnHelper<SymbolRow>();

const columns = [
  helper.accessor('symbol', {
    header: 'Symbol',
    cell: (info) => (
      <span className="font-mono font-medium text-cyan-400">{info.getValue()}</span>
    ),
  }),
  helper.accessor('exchange', { header: 'Exchange' }),
  helper.accessor('sector', { header: 'Sector' }),
  helper.accessor('tags', {
    header: 'Tags',
    cell: (info) => (
      <div className="flex flex-wrap gap-1">
        {info.getValue().map((t: string) => (
          <span key={t} className="rounded bg-gray-700 px-1.5 py-0.5 text-xs text-gray-300">
            {t}
          </span>
        ))}
      </div>
    ),
  }),
  helper.accessor('status', {
    header: 'Status',
    cell: (info) => {
      const v = info.getValue();
      return (
        <span
          className={`rounded px-2 py-0.5 text-xs font-medium ${
            v === 'active' ? 'bg-green-900 text-green-300' : 'bg-red-900 text-red-300'
          }`}
        >
          {v}
        </span>
      );
    },
  }),
];

export default function SymbolTable({ data, onSelect }: { data: SymbolRow[]; onSelect: (symbol: string) => void }) {
  const table = useReactTable({
    data,
    columns,
    getCoreRowModel: getCoreRowModel(),
  });

  return (
    <div className="overflow-x-auto rounded-lg border border-gray-700">
      <table className="min-w-full text-sm">
        <thead className="bg-gray-800 text-gray-300">
          {table.getHeaderGroups().map((hg) => (
            <tr key={hg.id}>
              {hg.headers.map((h) => (
                <th key={h.id} className="px-4 py-3 text-left font-medium">
                  {flexRender(h.column.columnDef.header, h.getContext())}
                </th>
              ))}
            </tr>
          ))}
        </thead>
        <tbody>
          {table.getRowModel().rows.map((row) => (
            <tr
              key={row.id}
              className="cursor-pointer border-t border-gray-700 hover:bg-gray-800"
              onClick={() => onSelect(row.original.symbol)}
            >
              {row.getVisibleCells().map((cell) => (
                <td key={cell.id} className="px-4 py-3">
                  {flexRender(cell.column.columnDef.cell, cell.getContext())}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
