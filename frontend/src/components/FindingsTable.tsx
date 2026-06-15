import React from 'react';
import Link from 'next/link';
import { SeverityBadge } from './SeverityBadge';
import { AnalyzerBadge } from './AnalyzerBadge';
import { ScorePill } from './ScorePill';
import { FindingResponse } from '@/lib/api';

export function FindingsTable({ findings }: { findings: FindingResponse[] }) {
  if (!findings || findings.length === 0) {
    return null; // Handled by EmptyState upstream
  }

  return (
    <div className="bg-surface border border-border rounded-[var(--r-card)] overflow-x-auto">
      <table className="w-full text-left text-sm whitespace-nowrap table-fixed">
        <thead className="bg-surface-sunken border-b border-border sticky top-0">
          <tr>
            <th className="w-24 px-4 py-3 font-medium text-text-muted">Severity</th>
            <th className="w-32 px-4 py-3 font-medium text-text-muted">Analyzer</th>
            <th className="w-32 px-4 py-3 font-medium text-text-muted">Entity ID</th>
            <th className="w-16 px-4 py-3 font-medium text-text-muted">Score</th>
            <th className="w-24 px-4 py-3 font-medium text-text-muted">Status</th>
            <th className="px-4 py-3 font-medium text-text-muted w-full">Summary</th>
            <th className="w-32 px-4 py-3 font-medium text-text-muted">Time</th>
          </tr>
        </thead>
        <tbody className="divide-y divide-border">
          {findings.map((f) => (
            <tr key={f.id} className="hover:bg-brand-weak/30 transition-colors group">
              <td className="px-4 py-3">
                <SeverityBadge band={f.band as any} />
              </td>
              <td className="px-4 py-3">
                <AnalyzerBadge analyzer={f.analyzer} />
              </td>
              <td className="px-4 py-3">
                <Link href={`/findings/${f.id}`} className="text-brand hover:underline font-medium">
                  {f.entity_id}
                </Link>
              </td>
              <td className="px-4 py-3">
                <ScorePill score={f.score || 0} band={f.band as any} />
              </td>
              <td className="px-4 py-3">
                <span className="capitalize text-text-muted text-xs font-medium border border-border px-2 py-0.5 rounded-[var(--r-control)] bg-canvas">
                  {f.status.replace('_', ' ')}
                </span>
              </td>
              <td className="px-4 py-3 truncate text-text-muted max-w-xs group-hover:text-text transition-colors">
                <Link href={`/findings/${f.id}`} className="block truncate">
                  {f.summary}
                </Link>
              </td>
              <td className="px-4 py-3 num text-text-muted text-xs">
                {new Date(f.created_at).toLocaleDateString()}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
