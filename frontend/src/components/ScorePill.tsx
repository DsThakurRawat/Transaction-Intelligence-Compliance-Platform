import React from 'react';
import { BAND, RiskBand } from '@/lib/severity';
import { cn } from '@/lib/utils';

interface ScorePillProps {
  score: number | null | undefined;
  band: string | null | undefined;
  variant?: 'compact' | 'large';
}

export function ScorePill({ score, band, variant = 'compact' }: ScorePillProps) {
  if (score === null || score === undefined) return <span className="text-text-muted">-</span>;
  
  const safeBand = (band && band in BAND) ? (band as RiskBand) : 'medium';
  const data = BAND[safeBand];

  return (
    <div 
      className={cn(
        "inline-flex items-center justify-center num rounded-[var(--r-control)] font-semibold border",
        variant === 'large' ? 'text-2xl px-4 py-2' : 'text-sm px-2 py-0.5'
      )}
      style={{ 
        backgroundColor: data.soft, 
        color: data.solid,
        borderColor: `${data.solid}40` // 25% opacity
      }}
    >
      {score.toFixed(1)}
    </div>
  );
}
