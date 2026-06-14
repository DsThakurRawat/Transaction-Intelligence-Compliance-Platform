import Link from "next/link";
import { fetchTopAccounts } from "@/lib/api";
import { Suspense } from "react";
import { Badge } from "@/components/Badge";

export const dynamic = 'force-dynamic';

async function AccountsTable() {
  try {
    const accounts = await fetchTopAccounts(50);

    return (
      <div className="bg-surface border border-border shadow-[0_1px_2px_rgba(21,33,59,0.04),0_2px_8px_rgba(21,33,59,0.06)] rounded-[var(--r-card)] overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-left border-collapse">
            <thead>
              <tr className="bg-surface-2 border-b border-border text-[12px] uppercase text-text-muted">
                <th className="px-6 py-3 font-semibold">Account ID</th>
                <th className="px-6 py-3 font-semibold text-right">Cumulative Risk Score</th>
                <th className="px-6 py-3 font-semibold text-center">Critical Flags</th>
              </tr>
            </thead>
            <tbody className="text-[14px]">
              {accounts.map(acc => (
                <tr key={acc.account_id} className="border-b border-border hover:bg-surface-2 transition-colors relative group">
                  <td className="px-6 py-4">
                    <Link href={`/transactions?account_id=${acc.account_id}`} className="absolute inset-0" />
                    <span className="num font-medium group-hover:text-brand transition-colors text-brand">{acc.account_id}</span>
                  </td>
                  <td className="px-6 py-4 text-right num font-semibold">{acc.total_score}</td>
                  <td className="px-6 py-4 text-center">
                    {acc.critical_flags > 0 ? (
                      <span className="inline-flex items-center justify-center w-6 h-6 rounded-full bg-risk-critical-soft text-risk-critical font-bold text-xs num">
                        {acc.critical_flags}
                      </span>
                    ) : (
                      <span className="text-text-muted num">0</span>
                    )}
                  </td>
                </tr>
              ))}
              {accounts.length === 0 && (
                <tr>
                  <td colSpan={3} className="px-6 py-12 text-center text-text-muted">No risky accounts found.</td>
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
        Couldn&apos;t load accounts. Check if the API is running.
      </div>
    );
  }
}

export default function AccountsPage() {
  return (
    <div className="max-w-4xl mx-auto flex flex-col gap-6">
      <div className="flex justify-between items-end">
        <div>
          <h1 className="text-2xl font-semibold mb-2">Riskiest Accounts</h1>
          <p className="text-text-muted">Accounts ranked by their cumulative risk scores across all flagged transactions.</p>
        </div>
      </div>
      
      <Suspense fallback={<div className="animate-pulse bg-surface-2 h-[400px] rounded-[var(--r-card)]"></div>}>
        <AccountsTable />
      </Suspense>
    </div>
  );
}
