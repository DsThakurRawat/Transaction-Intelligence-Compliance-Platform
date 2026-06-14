import Link from "next/link";
import { Badge } from "@/components/Badge";
import { RiskMeter } from "@/components/RiskMeter";
import { fetchTransactionDetail } from "@/lib/api";
import { ArrowLeft, ExternalLink, ShieldAlert, Cpu } from "lucide-react";
import { severityConfig } from "@/lib/severity";

export const dynamic = 'force-dynamic';

export default async function TransactionDetail({ params }: { params: { id: string } }) {
  try {
    const tx = await fetchTransactionDetail(params.id);
    const config = severityConfig[tx.band.toLowerCase()] || severityConfig['none'];

    return (
      <div className="max-w-4xl mx-auto flex flex-col gap-6 pb-12">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-4">
            <Link href="/transactions" className="flex items-center justify-center w-8 h-8 rounded-full hover:bg-surface-2 text-text-muted transition-colors">
              <ArrowLeft className="w-4 h-4" />
            </Link>
            <h1 className="text-xl font-semibold flex items-center gap-3">
              Transaction <span className="num font-normal text-text-muted">{tx.transaction_id}</span>
            </h1>
          </div>
          <Badge band={tx.band} />
        </div>

        {tx.explanation && (
          <div className="bg-surface border border-border rounded-[var(--r-card)] shadow-sm overflow-hidden flex flex-col relative">
            <div className="absolute top-0 left-0 w-1 h-full" style={{ backgroundColor: config.varSolid }}></div>
            <div className="px-6 py-5 border-b border-border bg-surface-2/30 flex gap-2 items-center">
              <ShieldAlert className="w-5 h-5" style={{ color: config.varSolid }} />
              <h2 className="font-semibold text-text">Why this was flagged</h2>
            </div>
            <div className="p-6 flex flex-col gap-4">
              <p className="text-[16px] leading-[26px] text-text">
                {tx.explanation.explanation}
              </p>
              <div className="flex items-center gap-3 mt-2 pt-4 border-t border-border">
                <span className="text-[12px] uppercase tracking-wider font-semibold text-text-muted">Suggested Action:</span>
                <span className="font-medium text-text capitalize">{tx.explanation.suggested_action}</span>
              </div>
            </div>
          </div>
        )}

        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div className="flex flex-col gap-6">
            <div className="bg-surface border border-border rounded-[var(--r-card)] p-6 shadow-sm flex flex-col gap-6">
              <h3 className="text-[12px] uppercase tracking-wider font-semibold text-text-muted">Risk Assessment</h3>
              <RiskMeter score={tx.score} band={tx.band} size="lg" />
              
              <div className="flex flex-col gap-3">
                <h4 className="text-sm font-medium">Triggered Rules</h4>
                <ul className="flex flex-col gap-2">
                  {tx.flags.map((flag, i) => (
                    <li key={i} className="flex gap-2 text-sm items-start">
                      <span className="text-risk-high mt-1">•</span>
                      <div className="flex flex-col">
                        <span className="font-medium">{flag.rule_name}</span>
                        <span className="text-text-muted text-xs">{flag.reason}</span>
                      </div>
                    </li>
                  ))}
                  {tx.flags.length === 0 && <span className="text-sm text-text-muted">No rules triggered</span>}
                </ul>
              </div>
            </div>
          </div>

          <div className="flex flex-col gap-6">
            <div className="bg-surface border border-border rounded-[var(--r-card)] overflow-hidden shadow-sm">
              <div className="px-6 py-4 border-b border-border bg-surface-2/30">
                <h3 className="text-[12px] uppercase tracking-wider font-semibold text-text-muted">Transaction Details</h3>
              </div>
              <div className="p-6 grid grid-cols-2 gap-y-6 gap-x-4">
                <div className="flex flex-col gap-1">
                  <span className="text-xs text-text-muted">Amount</span>
                  <span className="font-medium num text-lg">{tx.currency} {tx.amount.toLocaleString()}</span>
                </div>
                <div className="flex flex-col gap-1">
                  <span className="text-xs text-text-muted">Time</span>
                  <span className="font-medium num">{new Date(tx.timestamp).toLocaleString()}</span>
                </div>
                <div className="flex flex-col gap-1">
                  <span className="text-xs text-text-muted">Account</span>
                  <Link href={`/accounts/${tx.account_id}`} className="font-medium num text-brand flex items-center gap-1 hover:underline">
                    {tx.account_id} <ExternalLink className="w-3 h-3" />
                  </Link>
                </div>
                <div className="flex flex-col gap-1">
                  <span className="text-xs text-text-muted">Counterparty</span>
                  {tx.counterparty_account ? (
                    <span className="font-medium num">{tx.counterparty_account}</span>
                  ) : (
                    <span className="text-text-muted italic text-sm">None (Merchant txn)</span>
                  )}
                </div>
                <div className="flex flex-col gap-1">
                  <span className="text-xs text-text-muted">Merchant</span>
                  <span className="font-medium">{tx.merchant}</span>
                </div>
                <div className="flex flex-col gap-1">
                  <span className="text-xs text-text-muted">Location / Channel</span>
                  <span className="font-medium">{tx.country} · {tx.channel}</span>
                </div>
              </div>
            </div>

            {tx.baseline && (
              <div className="bg-surface border border-border rounded-[var(--r-card)] overflow-hidden shadow-sm">
                <div className="px-6 py-4 border-b border-border bg-surface-2/30 flex items-center justify-between">
                  <h3 className="text-[12px] uppercase tracking-wider font-semibold text-text-muted">Account Baseline</h3>
                  <Cpu className="w-4 h-4 text-text-muted" />
                </div>
                <div className="p-6 flex flex-col gap-4">
                  <div className="flex justify-between items-center text-sm">
                    <span className="text-text-muted">Normal Median Amount</span>
                    <span className="font-medium num">{tx.currency} {tx.baseline.amount_median.toLocaleString()}</span>
                  </div>
                  <div className="flex justify-between items-center text-sm">
                    <span className="text-text-muted">Total History</span>
                    <span className="font-medium num">{tx.baseline.tx_count} transactions</span>
                  </div>
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    );
  } catch (error) {
    return (
      <div className="p-6 bg-risk-critical-soft text-risk-critical rounded-[var(--r-card)] max-w-4xl mx-auto border border-risk-critical/20">
        Transaction not found or API error.
      </div>
    );
  }
}
