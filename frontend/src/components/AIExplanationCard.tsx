import React from 'react';
import { Sparkles } from 'lucide-react';

interface AIExplanationCardProps {
  text: string;
  status: string;
}

export function AIExplanationCard({ text, status }: AIExplanationCardProps) {
  return (
    <div className="bg-surface border border-border rounded-[var(--r-card)] overflow-hidden">
      <div className="bg-brand-ink/[0.02] border-b border-border px-5 py-3 flex items-center justify-between">
        <div className="flex items-center gap-2 text-text">
          <Sparkles className="w-4 h-4 text-brand" />
          <h3 className="text-sm font-semibold">AI-Assisted Analysis</h3>
        </div>
        {status === 'pending_review' && (
          <span className="text-[10px] font-semibold uppercase tracking-wider bg-brand-weak text-brand px-2 py-1 rounded-[var(--r-control)]">
            Pending Human Review
          </span>
        )}
      </div>
      <div className="p-5">
        <p className="text-sm text-text leading-relaxed whitespace-pre-wrap">{text}</p>
        <p className="text-xs text-text-muted mt-4 italic">
          This explanation was drafted by an LLM based on the finding's evidence. AI drafts do not constitute a final decision.
        </p>
      </div>
    </div>
  );
}
