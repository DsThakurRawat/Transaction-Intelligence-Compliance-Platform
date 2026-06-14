import React from 'react';

export function TopBar() {
  return (
    <header className="h-16 bg-surface border-b border-border flex items-center justify-between px-6 shrink-0">
      <h1 className="text-lg font-semibold text-text">Flagged Transactions</h1>
      <div className="flex items-center gap-4 text-sm text-text-muted">
        <div className="flex items-center gap-2">
          <span className="w-2 h-2 rounded-full bg-risk-clean"></span>
          System Active
        </div>
      </div>
    </header>
  );
}
