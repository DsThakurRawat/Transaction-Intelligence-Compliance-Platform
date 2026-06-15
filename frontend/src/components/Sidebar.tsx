'use client';
import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { LayoutDashboard, ShieldAlert, Users, Network } from 'lucide-react';
import { cn } from '@/lib/utils';

export function Sidebar() {
  const pathname = usePathname();
  
  const navItems = [
    { name: 'Overview', href: '/', icon: LayoutDashboard },
    { name: 'Findings', href: '/findings', icon: ShieldAlert },
    { name: 'Network', href: '/graph', icon: Network },
    { name: 'Accounts', href: '/accounts', icon: Users },
  ];

  return (
    <aside className="w-64 bg-brand text-surface h-full flex flex-col shrink-0">
      <div className="h-16 flex items-center px-6 border-b border-brand-ink/50">
        <div className="font-sans font-bold text-lg flex items-center gap-2">
          <div className="w-6 h-6 bg-surface rounded-sm flex items-center justify-center">
            <span className="text-brand text-xs font-bold">T</span>
          </div>
          TICP
        </div>
      </div>
      <div className="flex-1 py-6 px-4 flex flex-col gap-2">
        {navItems.map((item) => {
          const isActive = pathname === item.href || (item.href !== '/' && pathname.startsWith(item.href));
          return (
            <Link 
              key={item.name} 
              href={item.href}
              className={cn(
                "flex items-center gap-3 px-3 py-2 rounded-md text-sm font-medium transition-colors",
                isActive 
                  ? "bg-brand-ink text-surface" 
                  : "text-surface/70 hover:text-surface hover:bg-brand-ink/50"
              )}
            >
              <item.icon className="w-4 h-4" />
              {item.name}
            </Link>
          );
        })}
      </div>
    </aside>
  );
}
