import React from 'react';
import { LucideIcon } from 'lucide-react';

interface EmptyStateProps {
  icon: LucideIcon;
  title: string;
  hint: string;
  action?: React.ReactNode;
}

export function EmptyState({ icon: Icon, title, hint, action }: EmptyStateProps) {
  return (
    <div className="flex flex-col items-center justify-center p-12 text-center bg-surface border border-border rounded-[var(--r-card)] border-dashed">
      <div className="w-12 h-12 bg-surface-sunken rounded-full flex items-center justify-center mb-4">
        <Icon className="w-6 h-6 text-text-muted" />
      </div>
      <h3 className="text-lg font-medium text-text mb-2">{title}</h3>
      <p className="text-sm text-text-muted max-w-sm mx-auto mb-6">
        {hint}
      </p>
      {action}
    </div>
  );
}
