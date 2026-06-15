import React from 'react';
import Link from 'next/link';
import { ScorePill } from './ScorePill';
import { TopAccount } from '@/lib/api';

export function AccountsTable({ accounts }: { accounts: TopAccount[] }) {
  if (!accounts || accounts.length === 0) return null;

  const getBand = (score: number) => {
    if (score >= 90) return 'critical';
    if (score >= 70) return 'high';
    if (score >= 50) return 'medium';
    return 'low';
  };

  return (
    <div className="bg-surface border border-border rounded-[var(--r-card)] overflow-hidden">
      <table className="w-full text-left text-sm">
        <thead className="bg-surface-sunken border-b border-border">
          <tr>
            <th className="w-16 px-5 py-3 font-medium text-text-muted">Rank</th>
            <th className="px-5 py-3 font-medium text-text-muted">Account ID</th>
            <th className="w-32 px-5 py-3 font-medium text-text-muted">Risk Score</th>
            <th className="w-32 px-5 py-3 font-medium text-text-muted">Open Findings</th>
            <th className="w-32 px-5 py-3 font-medium text-text-muted">Actions</th>
          </tr>
        </thead>
        <tbody className="divide-y divide-border">
          {accounts.map((acc, idx) => (
            <tr key={acc.account_id} className="hover:bg-surface-sunken transition-colors">
              <td className="px-5 py-4 num text-text-muted">#{idx + 1}</td>
              <td className="px-5 py-4 font-medium text-text">
                {acc.account_id}
                {acc.critical_count > 0 && (
                  <span className="ml-2 inline-flex items-center px-2 py-0.5 rounded-[var(--r-control)] text-[10px] font-bold bg-risk-critical-soft text-risk-critical">
                    {acc.critical_count} CRITICAL
                  </span>
                )}
              </td>
              <td className="px-5 py-4">
                <ScorePill score={acc.total_score} band={getBand(acc.total_score)} />
              </td>
              <td className="px-5 py-4 num text-text-muted">
                {acc.finding_count}
              </td>
              <td className="px-5 py-4">
                <div className="flex gap-3">
                  <Link href={`/findings?analyzer=all&status=open`} className="text-brand hover:underline text-xs font-medium">
                    View
                  </Link>
                  <Link href={`/graph`} className="text-brand hover:underline text-xs font-medium">
                    Graph
                  </Link>
                </div>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
