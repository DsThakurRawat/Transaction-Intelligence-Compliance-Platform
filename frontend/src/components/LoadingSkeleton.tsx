import React from 'react';

export function LoadingSkeleton({ rows = 3 }: { rows?: number }) {
  return (
    <div className="animate-pulse flex flex-col gap-4 w-full">
      {Array.from({ length: rows }).map((_, i) => (
        <div key={i} className="h-16 bg-surface-sunken rounded-[var(--r-card)] border border-border"></div>
      ))}
    </div>
  );
}
