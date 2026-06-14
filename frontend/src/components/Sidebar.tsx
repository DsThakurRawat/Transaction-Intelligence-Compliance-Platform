'use client';
import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { LayoutDashboard, ListTree, Users, Network } from 'lucide-react';
import { cn } from '@/lib/utils';

export function Sidebar() {
  const pathname = usePathname();
  
  const navItems = [
    { name: 'Dashboard', href: '/', icon: LayoutDashboard },
    { name: 'Transactions', href: '/transactions', icon: ListTree },
    { name: 'Accounts', href: '/accounts', icon: Users },
    { name: 'Network Graph', href: '/graph', icon: Network },
  ];

  return (
    <aside className="w-64 bg-surface border-r border-border h-full flex flex-col shrink-0">
      <div className="h-16 flex items-center px-6 border-b border-border">
        <div className="font-sans font-bold text-lg text-brand flex items-center gap-2">
          <div className="w-6 h-6 bg-brand rounded-sm flex items-center justify-center">
            <span className="text-surface text-xs">A</span>
          </div>
          AML Detection
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
                  ? "bg-brand-weak text-brand" 
                  : "text-text-muted hover:text-text hover:bg-surface-2"
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
