import React from 'react';

export function EvidencePanel({ payload }: { payload: any }) {
  if (!payload || Object.keys(payload).length === 0) {
    return (
      <div className="p-4 border border-border rounded-[var(--r-card)] text-sm text-text-muted text-center bg-surface-sunken">
        No structured evidence available.
      </div>
    );
  }

  return (
    <div className="bg-surface border border-border rounded-[var(--r-card)] overflow-hidden">
      <div className="bg-surface-sunken border-b border-border px-5 py-3">
        <h3 className="text-sm font-semibold text-text">Evidence Data</h3>
      </div>
      <div className="p-0">
        <table className="w-full text-left text-sm">
          <tbody className="divide-y divide-border">
            {Object.entries(payload).map(([key, value], idx) => (
              <tr key={key} className={idx % 2 === 0 ? 'bg-surface' : 'bg-canvas'}>
                <td className="px-5 py-3 w-1/3 font-medium text-text-muted align-top capitalize">
                  {key.replace(/_/g, ' ')}
                </td>
                <td className="px-5 py-3 num text-text break-all">
                  {typeof value === 'object' && value !== null ? (
                    <pre className="text-xs bg-surface-sunken p-2 rounded-[var(--r-control)] border border-border overflow-x-auto">
                      {JSON.stringify(value, null, 2)}
                    </pre>
                  ) : (
                    String(value)
                  )}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
