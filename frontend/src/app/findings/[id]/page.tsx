import { fetchFindingDetail } from '@/lib/api';
import { SeverityBadge } from '@/components/SeverityBadge';
import { AnalyzerBadge } from '@/components/AnalyzerBadge';
import { ScorePill } from '@/components/ScorePill';
import { EvidencePanel } from '@/components/EvidencePanel';
import { AIExplanationCard } from '@/components/AIExplanationCard';
import { ErrorState } from '@/components/ErrorState';
import Link from 'next/link';

export const revalidate = 10;
export const dynamic = 'force-dynamic';

export default async function FindingDetailPage({ params }: { params: Promise<{ id: string }> }) {
  try {
    const { id } = await params;
    const finding = await fetchFindingDetail(id);

    return (
      <div className="max-w-4xl mx-auto flex flex-col gap-6 pb-12">
        <div className="flex items-center text-sm text-text-muted mb-2">
          <Link href="/findings" className="hover:text-text transition-colors">Findings</Link>
          <span className="mx-2">/</span>
          <span className="font-mono">{finding.id}</span>
        </div>

        {/* Header */}
        <div className="bg-surface border border-border rounded-[var(--r-card)] p-6 md:p-8 flex flex-col gap-6">
          <div className="flex flex-col md:flex-row md:items-start justify-between gap-4">
            <div className="flex flex-col gap-3">
              <div className="flex flex-wrap items-center gap-3">
                <SeverityBadge band={finding.band as any} />
                <AnalyzerBadge analyzer={finding.analyzer} />
                <span className="capitalize text-xs font-medium border border-border px-2 py-0.5 rounded-[var(--r-control)] bg-surface-sunken text-text-muted">
                  {finding.status.replace('_', ' ')}
                </span>
              </div>
              <h1 className="text-2xl font-bold text-text mt-2">{finding.entity_id}</h1>
              <p className="text-text-muted text-base">{finding.summary}</p>
            </div>
            <div className="shrink-0 flex flex-col items-end">
              <span className="text-xs font-medium text-text-muted uppercase tracking-wide mb-2">Risk Score</span>
              <ScorePill score={finding.score || 0} band={finding.band as any} variant="large" />
            </div>
          </div>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 items-start">
          <div className="flex flex-col gap-4">
            <h2 className="text-sm font-semibold uppercase tracking-wider text-text-muted">Investigation Evidence</h2>
            <EvidencePanel payload={finding.payload_json} />
          </div>
          
          {finding.explanation && (
            <div className="flex flex-col gap-4">
              <h2 className="text-sm font-semibold uppercase tracking-wider text-text-muted">AI Review</h2>
              <AIExplanationCard text={finding.explanation} status={finding.status} />
            </div>
          )}
        </div>
      </div>
    );
  } catch (error) {
    return (
      <div className="max-w-4xl mx-auto py-12">
        <ErrorState message="Finding not found or backend is offline." />
      </div>
    );
  }
}
