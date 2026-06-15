import React from 'react';
import { BAND, RiskBand } from '@/lib/severity';

export function SeverityBadge({ band }: { band: string | null | undefined }) {
  const safeBand = (band && band in BAND) ? (band as RiskBand) : 'medium';
  const data = BAND[safeBand];

  return (
    <span 
      className="inline-flex items-center gap-1.5 px-2 py-0.5 rounded-[var(--r-control)] text-xs font-medium"
      style={{ backgroundColor: data.soft, color: data.solid }}
    >
      <span className="w-1.5 h-1.5 rounded-full" style={{ backgroundColor: data.solid }}></span>
      {data.label}
    </span>
  );
}
