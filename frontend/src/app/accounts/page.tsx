import { fetchTopAccounts } from '@/lib/api';
import { AccountsTable } from '@/components/AccountsTable';
import { EmptyState } from '@/components/EmptyState';
import { ErrorState } from '@/components/ErrorState';
import { Users } from 'lucide-react';

export const revalidate = 10;
export const dynamic = 'force-dynamic';

export default async function AccountsPage() {
  try {
    const accounts = await fetchTopAccounts(50);

    return (
      <div className="flex flex-col max-w-7xl mx-auto h-full">
        <div className="flex flex-col gap-2 mb-6">
          <h1 className="text-xl font-semibold text-text">Riskiest Accounts</h1>
          <p className="text-sm text-text-muted">Accounts ranked by aggregated risk score across all active findings.</p>
        </div>

        {accounts.length === 0 ? (
          <EmptyState 
            icon={Users}
            title="No accounts found"
            hint="There are no active findings associated with accounts right now."
          />
        ) : (
          <AccountsTable accounts={accounts} />
        )}
      </div>
    );
  } catch (error) {
    return (
      <div className="max-w-7xl mx-auto py-12">
        <ErrorState message="Failed to fetch accounts. The backend may be offline." />
      </div>
    );
  }
}
