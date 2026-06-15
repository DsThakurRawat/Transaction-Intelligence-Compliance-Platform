import { fetchStats, fetchTopFindings } from '@/lib/api';
import { StatCard } from '@/components/StatCard';
import { AnalyzerCard } from '@/components/AnalyzerCard';
import { FindingsTable } from '@/components/FindingsTable';
import { EmptyState } from '@/components/EmptyState';
import { ErrorState } from '@/components/ErrorState';
import { Database } from 'lucide-react';

// Force dynamic rendering and revalidate every 10s
export const revalidate = 10;
export const dynamic = 'force-dynamic';

export default async function OverviewPage() {
  try {
    const [stats, topFindings] = await Promise.all([
      fetchStats(),
      fetchTopFindings(5)
    ]);

    const isSystemEmpty = stats.total_transactions === 0 && stats.total_findings === 0;

    return (
      <div className="flex flex-col gap-8 max-w-7xl mx-auto">
        <div className="flex flex-col gap-2">
          <h1 className="text-xl font-semibold text-text">Platform Overview</h1>
          <p className="text-sm text-text-muted">Unified compliance queue across all analyzers.</p>
        </div>

        {/* 1. Stat Cards Row */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          <StatCard 
            title="Total Transactions" 
            value={stats.total_transactions.toLocaleString()} 
            hint="Ingested payload"
          />
          <StatCard 
            title="Open Findings" 
            value={stats.total_findings.toLocaleString()} 
            hint="Across all analyzers"
          />
          <StatCard 
            title="Critical Risk" 
            value={stats.critical_findings.toLocaleString()} 
            band="critical"
            hint="Requires immediate action"
          />
          <StatCard 
            title="Accounts Monitored" 
            value={stats.active_accounts.toLocaleString()} 
          />
        </div>

        {/* 2. The Five Analyzers (Centerpiece) */}
        <div className="flex flex-col gap-4">
          <h2 className="text-base font-semibold text-text">Analyzer Status</h2>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-5 gap-6">
            <AnalyzerCard 
              analyzer="aml" 
              count={stats.by_analyzer.aml || 0} 
              metricLabel="Critical Structuring" 
              metricValue={stats.critical_findings} 
              topBand={stats.by_analyzer.aml > 0 ? 'critical' : 'clean'}
            />
            <AnalyzerCard 
              analyzer="reconciliation" 
              count={stats.by_analyzer.reconciliation || 0} 
              metricLabel="Open Breaks" 
              metricValue={stats.by_analyzer.reconciliation || 0}
              topBand={stats.by_analyzer.reconciliation > 0 ? 'high' : 'clean'}
            />
            <AnalyzerCard 
              analyzer="categorization" 
              count={stats.by_analyzer.categorization || 0} 
              metricLabel="Needs Review" 
              metricValue={stats.by_analyzer.categorization || 0}
              topBand={stats.by_analyzer.categorization > 0 ? 'medium' : 'clean'}
            />
            <AnalyzerCard 
              analyzer="disputes" 
              count={stats.by_analyzer.disputes || 0} 
              metricLabel="Deadlines ≤ 7d" 
              metricValue={0} // Placeholder for disputes deadline logic
              topBand={stats.by_analyzer.disputes > 0 ? 'high' : 'clean'}
            />
            <AnalyzerCard 
              analyzer="reporting" 
              count={stats.by_analyzer.reporting || 0} 
              metricLabel="SARs Pending" 
              metricValue={stats.by_analyzer.reporting || 0}
              topBand={stats.by_analyzer.reporting > 0 ? 'medium' : 'clean'}
            />
          </div>
        </div>

        {/* 3. Top Critical Findings Strip */}
        <div className="flex flex-col gap-4">
          <h2 className="text-base font-semibold text-text">Top Critical Findings</h2>
          {isSystemEmpty ? (
            <EmptyState 
              icon={Database}
              title="Awaiting Data"
              hint="The database is currently empty. Run the analyzers via the CLI to populate the dashboard."
            />
          ) : (
            <FindingsTable findings={topFindings} />
          )}
        </div>
      </div>
    );
  } catch (error) {
    return (
      <div className="max-w-7xl mx-auto py-12">
        <ErrorState message="Could not connect to the backend. The API may be cold-starting or offline." />
      </div>
    );
  }
}
