import Link from "next/link";
import { SummaryCard } from "@/components/SummaryCard";
import { Badge } from "@/components/Badge";
import { RiskMeter } from "@/components/RiskMeter";
import { fetchStats, fetchTopFindings } from "@/lib/api";
import { Suspense } from "react";

export const dynamic = 'force-dynamic';

async function DashboardContent() {
  try {
    const [stats, topFindings] = await Promise.all([
      fetchStats(),
      fetchTopFindings(10)
    ]);

    const criticalCount = stats.by_band["critical"] || 0;
    const highCount = stats.by_band["high"] || 0;

    return (
      <div className="flex flex-col gap-8">
        <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
          <SummaryCard title="Total Findings" value={stats.total.toLocaleString()} />
          <SummaryCard title="Critical Risk" value={criticalCount.toLocaleString()} band="critical" />
          <SummaryCard title="High Risk" value={highCount.toLocaleString()} band="high" />
          <SummaryCard title="AML Alerts" value={(stats.by_analyzer["aml"] || 0).toLocaleString()} />
        </div>
        
        <div className="bg-surface border border-border shadow-[0_1px_2px_rgba(21,33,59,0.04),0_2px_8px_rgba(21,33,59,0.06)] rounded-[var(--r-card)] overflow-hidden">
          <div className="px-6 py-4 border-b border-border bg-surface-2/50 flex justify-between items-center">
            <h2 className="text-lg font-semibold">Top Priority Findings</h2>
            <Link href="/findings" className="text-sm font-medium text-brand hover:underline">
              View All
            </Link>
          </div>
          <div className="overflow-x-auto">
            <table className="w-full text-left border-collapse">
              <thead>
                <tr className="bg-surface-2 border-b border-border text-[12px] uppercase text-text-muted">
                  <th className="px-6 py-3 font-semibold">Finding ID</th>
                  <th className="px-6 py-3 font-semibold">Analyzer</th>
                  <th className="px-6 py-3 font-semibold">Entity</th>
                  <th className="px-6 py-3 font-semibold text-right">Risk Score</th>
                  <th className="px-6 py-3 font-semibold">Severity</th>
                </tr>
              </thead>
              <tbody className="text-[14px]">
                {topFindings.map(f => (
                  <tr key={f.id} className="border-b border-border hover:bg-surface-2 transition-colors relative group">
                    <td className="px-6 py-4">
                      <Link href={`/findings/${f.id}`} className="absolute inset-0" />
                      <span className="num font-medium group-hover:text-brand transition-colors">{f.id.substring(0, 8)}...</span>
                    </td>
                    <td className="px-6 py-4 capitalize">{f.analyzer}</td>
                    <td className="px-6 py-4 num">{f.entity_id.substring(0, 8)}...</td>
                    <td className="px-6 py-4 text-right">
                      <div className="flex justify-end">
                        {f.score ? <RiskMeter score={f.score} band={f.band || "medium"} /> : "-"}
                      </div>
                    </td>
                    <td className="px-6 py-4">
                      <Badge band={f.band || "medium"} />
                    </td>
                  </tr>
                ))}
                {topFindings.length === 0 && (
                  <tr>
                    <td colSpan={5} className="px-6 py-8 text-center text-text-muted">No findings right now.</td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        </div>
      </div>
    );
  } catch (error) {
    return (
      <div className="p-6 bg-risk-critical-soft text-risk-critical rounded-[var(--r-card)]">
        Couldn&apos;t load dashboard data. Check if the API is running.
      </div>
    );
  }
}

export default function Home() {
  return (
    <div className="max-w-6xl mx-auto flex flex-col gap-6">
      <div>
        <h1 className="text-2xl font-semibold mb-2">Platform Dashboard</h1>
        <p className="text-text-muted">Unified view of AML, Reconciliation, and Disputes.</p>
      </div>
      
      <Suspense fallback={<div className="animate-pulse bg-surface-2 h-96 rounded-[var(--r-card)]"></div>}>
        <DashboardContent />
      </Suspense>
    </div>
  );
}
