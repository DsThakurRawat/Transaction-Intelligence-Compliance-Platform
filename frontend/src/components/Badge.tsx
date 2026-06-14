import React from 'react';
import { severityConfig, RiskBand } from '@/lib/severity';
import { cn } from '@/lib/utils';

interface BadgeProps {
  band: string;
  className?: string;
}

export function Badge({ band, className }: BadgeProps) {
  const config = severityConfig[band.toLowerCase()] || severityConfig['none'];
  
  return (
    <span 
      className={cn("inline-flex items-center justify-center px-[10px] py-[2px] rounded-full text-[12px] font-semibold tracking-wider", className)}
      style={{
        backgroundColor: config.varSoft,
        color: config.varSolid
      }}
    >
      {config.label}
    </span>
  );
}
