import React from 'react';
import { cn } from '@/lib/utils';

interface StatCardProps {
  title: string;
  value: string | number;
  hint?: string;
  band?: 'critical' | 'high' | 'medium' | 'low' | 'clean';
}

export function StatCard({ title, value, hint, band }: StatCardProps) {
  return (
    <div className={cn(
      "bg-surface-sunken border border-border rounded-[var(--r-card)] p-4 flex flex-col justify-between",
      band === 'critical' ? 'border-risk-critical/20 bg-risk-critical-soft/50' : '',
      band === 'high' ? 'border-risk-high/20 bg-risk-high-soft/50' : ''
    )}>
      <h3 className="text-[12px] font-medium text-text-muted uppercase tracking-wide mb-2">{title}</h3>
      <div className="flex items-baseline gap-2">
        <span className={cn(
          "num text-2xl font-medium",
          band === 'critical' ? 'text-risk-critical' : '',
          band === 'high' ? 'text-risk-high' : ''
        )}>
          {value}
        </span>
        {hint && <span className="text-xs text-text-muted">{hint}</span>}
      </div>
    </div>
  );
}
