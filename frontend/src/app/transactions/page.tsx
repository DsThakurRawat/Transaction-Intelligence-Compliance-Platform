import Link from "next/link";
import { Badge } from "@/components/Badge";
import { RiskMeter } from "@/components/RiskMeter";
import { fetchTransactions } from "@/lib/api";
import { Suspense } from "react";
import { severityConfig } from "@/lib/severity";

export const dynamic = 'force-dynamic';

async function TransactionsTable({ searchParams }: { searchParams: { band?: string, page?: string } }) {
  const page = parseInt(searchParams.page || "1", 10);
  const limit = 50;
  const offset = (page - 1) * limit;
  const band = searchParams.band;
  
  try {
    const transactions = await fetchTransactions(limit, offset, band);

    return (
      <div className="bg-surface border border-border shadow-[0_1px_2px_rgba(21,33,59,0.04),0_2px_8px_rgba(21,33,59,0.06)] rounded-[var(--r-card)] overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-left border-collapse">
            <thead>
              <tr className="bg-surface-2 border-b border-border text-[12px] uppercase text-text-muted">
                <th className="w-1 px-0"></th>
                <th className="px-4 py-3 font-semibold">Transaction ID</th>
                <th className="px-4 py-3 font-semibold">Score</th>
                <th className="px-4 py-3 font-semibold">Band</th>
                <th className="px-4 py-3 font-semibold">Account</th>
                <th className="px-4 py-3 font-semibold text-right">Amount</th>
                <th className="px-4 py-3 font-semibold">Time</th>
              </tr>
            </thead>
            <tbody className="text-[14px]">
              {transactions.map(tx => {
                const config = severityConfig[tx.band.toLowerCase()] || severityConfig['none'];
                return (
                  <tr key={tx.transaction_id} className="border-b border-border hover:bg-surface-2 transition-colors relative group">
                    <td className="w-1 px-0" style={{ backgroundColor: config.varSolid }}></td>
                    <td className="px-4 py-4">
                      <Link href={`/transactions/${tx.transaction_id}`} className="absolute inset-0" />
                      <span className="num font-medium group-hover:text-brand transition-colors">{tx.transaction_id.substring(0, 8)}...</span>
                    </td>
                    <td className="px-4 py-4">
                      <RiskMeter score={tx.score} band={tx.band} />
                    </td>
                    <td className="px-4 py-4"><Badge band={tx.band} /></td>
                    <td className="px-4 py-4 num">{tx.account_id}</td>
                    <td className="px-4 py-4 num text-right">{tx.currency} {tx.amount.toLocaleString()}</td>
                    <td className="px-4 py-4 num text-text-muted">{new Date(tx.timestamp).toLocaleString()}</td>
                  </tr>
                );
              })}
              {transactions.length === 0 && (
                <tr>
                  <td colSpan={7} className="px-6 py-12 text-center text-text-muted">No flagged transactions in this range.</td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>
    );
  } catch (error) {
    return (
      <div className="p-6 bg-risk-critical-soft text-risk-critical rounded-[var(--r-card)] border border-risk-critical/20">
        Couldn&apos;t load transactions. Check if the API is running.
      </div>
    );
  }
}

export default function TransactionsPage({ searchParams }: { searchParams: { band?: string, page?: string } }) {
  return (
    <div className="max-w-6xl mx-auto flex flex-col gap-6">
      <div className="flex justify-between items-end">
        <div>
          <h1 className="text-2xl font-semibold mb-2">Transactions</h1>
          <p className="text-text-muted">All flagged and scored transactions.</p>
        </div>
        <div className="flex gap-2">
          {/* Simple Band Filter Links */}
          <Link href="/transactions" className="px-3 py-1.5 bg-surface border border-border rounded-md text-sm hover:bg-surface-2 transition-colors">All</Link>
          <Link href="/transactions?band=critical" className="px-3 py-1.5 bg-surface border border-border rounded-md text-sm hover:bg-surface-2 transition-colors">Critical</Link>
          <Link href="/transactions?band=high" className="px-3 py-1.5 bg-surface border border-border rounded-md text-sm hover:bg-surface-2 transition-colors">High</Link>
        </div>
      </div>
      
      <Suspense fallback={<div className="animate-pulse bg-surface-2 h-[600px] rounded-[var(--r-card)]"></div>}>
        <TransactionsTable searchParams={searchParams} />
      </Suspense>
    </div>
  );
}
