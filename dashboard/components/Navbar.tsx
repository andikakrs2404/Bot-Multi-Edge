'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { BarChart3, Radio, Server } from 'lucide-react';

const links = [
  { href: '/system', label: 'System', icon: Server },
  { href: '/symbols', label: 'Symbols', icon: BarChart3 },
];

export default function Navbar() {
  const path = usePathname();

  return (
    <nav className="border-b border-gray-800 bg-gray-900/80 backdrop-blur">
      <div className="mx-auto flex max-w-7xl items-center justify-between px-4 py-3 sm:px-6 lg:px-8">
        <div className="flex items-center gap-2">
          <Radio className="h-5 w-5 text-cyan-400" />
          <span className="text-lg font-semibold text-white">Trading Bot</span>
        </div>
        <div className="flex gap-1">
          {links.map((l) => {
            const active = path.startsWith(l.href);
            return (
              <Link
                key={l.href}
                href={l.href}
                className={`flex items-center gap-1.5 rounded-md px-3 py-1.5 text-sm font-medium transition-colors ${
                  active
                    ? 'bg-gray-800 text-white'
                    : 'text-gray-400 hover:text-gray-200'
                }`}
              >
                <l.icon className="h-4 w-4" />
                {l.label}
              </Link>
            );
          })}
        </div>
      </div>
    </nav>
  );
}
