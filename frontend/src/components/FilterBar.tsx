'use client';
import React, { useCallback } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import { cn } from '@/lib/utils';

export function FilterBar() {
  const router = useRouter();
  const searchParams = useSearchParams();

  const currentAnalyzer = searchParams.get('analyzer') || 'all';
  const currentBand = searchParams.get('band') || '';
  const currentStatus = searchParams.get('status') || '';

  const createQueryString = useCallback(
    (name: string, value: string) => {
      const params = new URLSearchParams(searchParams.toString());
      if (value && value !== 'all') {
        params.set(name, value);
      } else {
        params.delete(name);
      }
      return params.toString();
    },
    [searchParams]
  );

  const tabs = ['all', 'aml', 'reconciliation', 'categorization', 'disputes', 'reporting'];

  return (
    <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 bg-surface border border-border rounded-[var(--r-card)] p-2 mb-6">
      <div className="flex overflow-x-auto no-scrollbar gap-1">
        {tabs.map(tab => (
          <button
            key={tab}
            onClick={() => router.push(`/findings?${createQueryString('analyzer', tab)}`)}
            className={cn(
              "px-4 py-2 text-sm font-medium rounded-[var(--r-control)] capitalize whitespace-nowrap transition-colors",
              currentAnalyzer === tab 
                ? "bg-brand text-surface shadow-sm" 
                : "text-text-muted hover:text-text hover:bg-surface-sunken"
            )}
          >
            {tab}
          </button>
        ))}
      </div>
      
      <div className="flex items-center gap-2 px-2 md:px-0">
        <select
          className="bg-surface-sunken border border-border text-text text-sm rounded-[var(--r-control)] focus:ring-1 focus:ring-brand focus:border-brand block px-3 py-2 outline-none"
          value={currentBand}
          onChange={(e) => router.push(`/findings?${createQueryString('band', e.target.value)}`)}
        >
          <option value="">All Severities</option>
          <option value="critical">Critical</option>
          <option value="high">High</option>
          <option value="medium">Medium</option>
          <option value="low">Low</option>
          <option value="clean">Clean</option>
        </select>

        <select
          className="bg-surface-sunken border border-border text-text text-sm rounded-[var(--r-control)] focus:ring-1 focus:ring-brand focus:border-brand block px-3 py-2 outline-none"
          value={currentStatus}
          onChange={(e) => router.push(`/findings?${createQueryString('status', e.target.value)}`)}
        >
          <option value="">All Statuses</option>
          <option value="open">Open</option>
          <option value="pending_review">Pending Review</option>
          <option value="resolved">Resolved</option>
        </select>
      </div>
    </div>
  );
}
