import React from 'react';
import { ShieldAlert, ArrowLeftRight, Tags, Gavel, FileText } from 'lucide-react';
import { BAND, RiskBand } from '@/lib/severity';
import Link from 'next/link';

interface AnalyzerCardProps {
  analyzer: 'aml' | 'reconciliation' | 'categorization' | 'disputes' | 'reporting';
  count: number;
  metricLabel: string;
  metricValue: string | number;
  topBand?: RiskBand;
}

const ICONS = {
  aml: ShieldAlert,
  reconciliation: ArrowLeftRight,
  categorization: Tags,
  disputes: Gavel,
  reporting: FileText
};

const NAMES = {
  aml: 'AML',
  reconciliation: 'Reconciliation',
  categorization: 'Categorization',
  disputes: 'Disputes',
  reporting: 'Reporting'
};

export function AnalyzerCard({ analyzer, count, metricLabel, metricValue, topBand }: AnalyzerCardProps) {
  const Icon = ICONS[analyzer];
  const bandData = topBand ? BAND[topBand] : null;

  return (
    <Link 
      href={`/findings?analyzer=${analyzer}`}
      className="block bg-surface border border-border rounded-[var(--r-card)] p-5 hover:border-brand/30 hover:shadow-[0_2px_8px_rgba(21,33,59,0.08)] transition-all group"
    >
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-2 text-text-muted group-hover:text-brand transition-colors">
          <Icon className="w-5 h-5" />
          <h3 className="font-semibold text-sm capitalize">{NAMES[analyzer]}</h3>
        </div>
        {bandData && (
          <div 
            className="w-2.5 h-2.5 rounded-full" 
            style={{ backgroundColor: bandData.solid }}
            title={`Worst current risk: ${bandData.label}`}
          />
        )}
      </div>
      
      <div className="mb-4">
        <div className="text-3xl num font-medium text-text">{count.toLocaleString()}</div>
        <div className="text-[12px] font-medium text-text-muted uppercase tracking-wide">Open Findings</div>
      </div>
      
      <div className="pt-3 border-t border-border flex justify-between items-end">
        <span className="text-[12px] text-text-muted">{metricLabel}</span>
        <span className="num text-sm font-medium">{metricValue}</span>
      </div>
    </Link>
  );
}
