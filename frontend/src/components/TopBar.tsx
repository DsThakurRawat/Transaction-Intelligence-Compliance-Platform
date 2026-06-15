'use client';
import React, { useEffect, useState } from 'react';
import { usePathname } from 'next/navigation';

export function TopBar() {
  const pathname = usePathname();
  const [healthOk, setHealthOk] = useState<boolean | null>(null);

  useEffect(() => {
    const checkHealth = async () => {
      try {
        const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://127.0.0.1:8000';
        const res = await fetch(`${API_BASE}/health`);
        setHealthOk(res.ok);
      } catch (e) {
        setHealthOk(false);
      }
    };
    
    checkHealth();
    const interval = setInterval(checkHealth, 30000); // Poll every 30s
    return () => clearInterval(interval);
  }, []);

  const getTitle = () => {
    if (pathname === '/') return 'Platform Overview';
    if (pathname.startsWith('/findings')) return 'Review Findings';
    if (pathname.startsWith('/graph')) return 'Network Graph';
    if (pathname.startsWith('/accounts')) return 'Account Risk';
    return 'Dashboard';
  };

  return (
    <header className="h-16 bg-surface border-b border-border flex items-center justify-between px-6 shrink-0">
      <h1 className="text-lg font-semibold text-text">{getTitle()}</h1>
      <div className="flex items-center gap-4 text-sm text-text-muted">
        <div className="flex items-center gap-2" title={healthOk ? "API Connected" : "API Unreachable"}>
          <span className={`w-2 h-2 rounded-full ${healthOk === true ? 'bg-risk-clean' : healthOk === false ? 'bg-risk-critical' : 'bg-surface-sunken'}`}></span>
          {healthOk === true ? 'System Active' : healthOk === false ? 'System Offline' : 'Connecting...'}
        </div>
      </div>
    </header>
  );
}
