import React from 'react';
import { AlertCircle } from 'lucide-react';

export function ErrorState({ message }: { message: string }) {
  return (
    <div className="flex flex-col items-center justify-center p-8 text-center bg-risk-critical-soft/50 border border-risk-critical/20 rounded-[var(--r-card)]">
      <AlertCircle className="w-8 h-8 text-risk-critical mb-3" />
      <p className="text-sm font-medium text-risk-critical">{message}</p>
    </div>
  );
}
