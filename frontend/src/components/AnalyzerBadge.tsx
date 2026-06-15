import React from 'react';
import { ShieldAlert, ArrowLeftRight, Tags, Gavel, FileText } from 'lucide-react';

interface AnalyzerBadgeProps {
  analyzer: string;
}

const ICONS: Record<string, any> = {
  aml: ShieldAlert,
  reconciliation: ArrowLeftRight,
  categorization: Tags,
  disputes: Gavel,
  reporting: FileText
};

export function AnalyzerBadge({ analyzer }: AnalyzerBadgeProps) {
  const Icon = ICONS[analyzer.toLowerCase()] || ShieldAlert;
  
  return (
    <span className="inline-flex items-center gap-1.5 px-2 py-0.5 rounded-[var(--r-control)] bg-surface-sunken text-text-muted text-xs font-medium border border-border">
      <Icon className="w-3 h-3" />
      <span className="capitalize">{analyzer}</span>
    </span>
  );
}
