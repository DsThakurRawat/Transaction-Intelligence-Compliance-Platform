import React from 'react';
import { severityConfig, RiskBand } from '@/lib/severity';
import { cn } from '@/lib/utils';

interface RiskMeterProps {
  score: number;
  band: string;
  size?: 'sm' | 'lg';
  className?: string;
}

export function RiskMeter({ score, band, size = 'sm', className }: RiskMeterProps) {
  const config = severityConfig[band.toLowerCase()] || severityConfig['none'];
  
  const height = size === 'lg' ? '12px' : '6px';
  const scoreClass = size === 'lg' ? 'text-[32px] leading-[36px]' : 'text-[14px] leading-[20px]';
  const width = size === 'lg' ? 'w-full' : 'w-[80px]';

  return (
    <div className={cn("flex flex-col gap-1", className)}>
      <div className={cn("font-semibold num", scoreClass)} style={{ color: config.varSolid }}>
        {score} <span className={size === 'lg' ? 'text-text-muted text-[18px]' : 'text-text-muted text-[12px]'}>/ 100</span>
      </div>
      <div className={cn("bg-surface-2 overflow-hidden rounded-full", width)} style={{ height }}>
        <div 
          className="h-full transition-all duration-300 ease-out" 
          style={{ 
            width: `${score}%`, 
            backgroundColor: config.varSolid 
          }} 
        />
      </div>
    </div>
  );
}
