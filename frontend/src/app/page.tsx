import Link from "next/link";
import { SummaryCard } from "@/components/SummaryCard";
import { Badge } from "@/components/Badge";
import { RiskMeter } from "@/components/RiskMeter";
import { fetchStats, fetchTopTransactions } from "@/lib/api";
import { Suspense } from "react";

export const dynamic = 'force-dynamic';

async function DashboardContent() {
  try {
    const [stats, topTx] = await Promise.all([
      fetchStats(),
      fetchTopTransactions(10)
    ]);

    const criticalCount = stats.by_band["critical"] || 0;
    const highCount = stats.by_band["high"] || 0;

    return (
      <div className="flex flex-col gap-8">
        <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
          <SummaryCard title="Total Flagged" value={stats.total_flagged.toLocaleString()} />
          <SummaryCard title="Critical Risk" value={criticalCount.toLocaleString()} band="critical" />
          <SummaryCard title="High Risk" value={highCount.toLocaleString()} band="high" />
          <SummaryCard title="Explanations" value={stats.explanations_generated.toLocaleString()} />
        </div>
        
        <div className="bg-surface border border-border shadow-[0_1px_2px_rgba(21,33,59,0.04),0_2px_8px_rgba(21,33,59,0.06)] rounded-[var(--r-card)] overflow-hidden">
          <div className="px-6 py-4 border-b border-border bg-surface-2/50 flex justify-between items-center">
            <h2 className="text-lg font-semibold">Top Riskiest Transactions</h2>
            <Link href="/transactions" className="text-sm font-medium text-brand hover:underline">
              View All
            </Link>
          </div>
          <div className="overflow-x-auto">
            <table className="w-full text-left border-collapse">
              <thead>
                <tr className="bg-surface-2 border-b border-border text-[12px] uppercase text-text-muted">
                  <th className="px-6 py-3 font-semibold">Transaction ID</th>
                  <th className="px-6 py-3 font-semibold">Account ID</th>
                  <th className="px-6 py-3 font-semibold text-right">Risk Score</th>
                  <th className="px-6 py-3 font-semibold">Severity</th>
                </tr>
              </thead>
              <tbody className="text-[14px]">
                {topTx.map(tx => (
                  <tr key={tx.transaction_id} className="border-b border-border hover:bg-surface-2 transition-colors relative group">
                    <td className="px-6 py-4">
                      <Link href={`/transactions/${tx.transaction_id}`} className="absolute inset-0" />
                      <span className="num font-medium group-hover:text-brand transition-colors">{tx.transaction_id.substring(0, 8)}...</span>
                    </td>
                    <td className="px-6 py-4 num">{tx.account_id}</td>
                    <td className="px-6 py-4 text-right">
                      <div className="flex justify-end">
                        <RiskMeter score={tx.score} band={tx.band} />
                      </div>
                    </td>
                    <td className="px-6 py-4">
                      <Badge band={tx.band} />
                    </td>
                  </tr>
                ))}
                {topTx.length === 0 && (
                  <tr>
                    <td colSpan={4} className="px-6 py-8 text-center text-text-muted">No flagged transactions found.</td>
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
        <h1 className="text-2xl font-semibold mb-2">Dashboard</h1>
        <p className="text-text-muted">Overview of recent AML and fraud flags.</p>
      </div>
      
      <Suspense fallback={<div className="animate-pulse bg-surface-2 h-96 rounded-[var(--r-card)]"></div>}>
        <DashboardContent />
      </Suspense>
    </div>
  );
}
