import Link from "next/link";
import { Badge } from "@/components/Badge";
import { RiskMeter } from "@/components/RiskMeter";
import { fetchFindingDetail } from "@/lib/api";
import { ArrowLeft, ExternalLink, ShieldAlert, FileText, CheckCircle } from "lucide-react";
import { severityConfig } from "@/lib/severity";

export const dynamic = 'force-dynamic';

export default async function FindingDetail({ params }: { params: { id: string } }) {
  try {
    const f = await fetchFindingDetail(params.id);
    const config = severityConfig[f.band?.toLowerCase() || 'none'] || severityConfig['none'];

    return (
      <div className="max-w-4xl mx-auto flex flex-col gap-6 pb-12">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-4">
            <Link href="/findings" className="flex items-center justify-center w-8 h-8 rounded-full hover:bg-surface-2 text-text-muted transition-colors">
              <ArrowLeft className="w-4 h-4" />
            </Link>
            <h1 className="text-xl font-semibold flex items-center gap-3">
              Finding <span className="num font-normal text-text-muted">{f.id}</span>
            </h1>
          </div>
          <Badge band={f.band || "medium"} />
        </div>

        {f.explanation && (
          <div className="bg-surface border border-border rounded-[var(--r-card)] shadow-sm overflow-hidden flex flex-col relative">
            <div className="absolute top-0 left-0 w-1 h-full" style={{ backgroundColor: config.varSolid }}></div>
            <div className="px-6 py-5 border-b border-border bg-surface-2/30 flex gap-2 items-center">
              <ShieldAlert className="w-5 h-5" style={{ color: config.varSolid }} />
              <h2 className="font-semibold text-text">AI Explanation</h2>
            </div>
            <div className="p-6 flex flex-col gap-4">
              <p className="text-[16px] leading-[26px] text-text whitespace-pre-wrap">
                {f.explanation}
              </p>
            </div>
          </div>
        )}

        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div className="flex flex-col gap-6">
            <div className="bg-surface border border-border rounded-[var(--r-card)] p-6 shadow-sm flex flex-col gap-6">
              <h3 className="text-[12px] uppercase tracking-wider font-semibold text-text-muted">Assessment</h3>
              {f.score !== null ? <RiskMeter score={f.score} band={f.band || "medium"} size="lg" /> : <div className="text-text-muted py-4">No specific score assigned</div>}
              
              <div className="flex flex-col gap-3">
                <h4 className="text-sm font-medium">Summary</h4>
                <p className="text-sm">{f.summary}</p>
                <div className="flex gap-2 text-sm mt-2">
                  <span className="font-medium">Analyzer:</span>
                  <span className="capitalize">{f.analyzer}</span>
                </div>
                <div className="flex gap-2 text-sm">
                  <span className="font-medium">Status:</span>
                  <span className="capitalize">{f.status.replace('_', ' ')}</span>
                </div>
              </div>
            </div>
          </div>

          <div className="flex flex-col gap-6">
            <div className="bg-surface border border-border rounded-[var(--r-card)] overflow-hidden shadow-sm">
              <div className="px-6 py-4 border-b border-border bg-surface-2/30">
                <h3 className="text-[12px] uppercase tracking-wider font-semibold text-text-muted">Entity Context</h3>
              </div>
              <div className="p-6 grid grid-cols-1 gap-y-6">
                <div className="flex flex-col gap-1">
                  <span className="text-xs text-text-muted">Entity Type</span>
                  <span className="font-medium capitalize">{f.entity_type}</span>
                </div>
                <div className="flex flex-col gap-1">
                  <span className="text-xs text-text-muted">Entity ID</span>
                  <span className="font-medium num break-all">{f.entity_id}</span>
                </div>
                <div className="flex flex-col gap-1">
                  <span className="text-xs text-text-muted">Finding Type</span>
                  <span className="font-medium">{f.finding_type}</span>
                </div>
                <div className="flex flex-col gap-1">
                  <span className="text-xs text-text-muted">Time Detected</span>
                  <span className="font-medium num">{new Date(f.created_at).toLocaleString()}</span>
                </div>
              </div>
            </div>
            
            {f.payload_json && Object.keys(f.payload_json).length > 0 && (
              <div className="bg-surface border border-border rounded-[var(--r-card)] overflow-hidden shadow-sm">
                <div className="px-6 py-4 border-b border-border bg-surface-2/30 flex items-center justify-between">
                  <h3 className="text-[12px] uppercase tracking-wider font-semibold text-text-muted">Payload Details</h3>
                  <FileText className="w-4 h-4 text-text-muted" />
                </div>
                <div className="p-6 flex flex-col gap-4">
                  <pre className="text-xs bg-surface-2 p-3 rounded text-text-muted overflow-x-auto">
                    {JSON.stringify(f.payload_json, null, 2)}
                  </pre>
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
        Finding not found or API error.
      </div>
    );
  }
}
