import React from 'react';
import { cn } from '@/lib/utils';
import { severityConfig } from '@/lib/severity';

interface SummaryCardProps {
  title: string;
  value: string | number;
  band?: string;
  className?: string;
}

export function SummaryCard({ title, value, band, className }: SummaryCardProps) {
  let valueColor = 'var(--text)';
  if (band && severityConfig[band.toLowerCase()]) {
    valueColor = severityConfig[band.toLowerCase()].varSolid;
  }

  return (
    <div className={cn("bg-surface border border-border shadow-[0_1px_2px_rgba(21,33,59,0.04),0_2px_8px_rgba(21,33,59,0.06)] rounded-[var(--r-card)] p-5 flex flex-col gap-2", className)}>
      <h3 className="text-[12px] leading-[16px] tracking-[0.04em] uppercase font-semibold text-text-muted">
        {title}
      </h3>
      <div 
        className="text-[32px] leading-[36px] font-semibold num"
        style={{ color: valueColor }}
      >
        {value}
      </div>
    </div>
  );
}
