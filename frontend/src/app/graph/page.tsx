import { fetchGraphData } from '@/lib/api';
import NetworkGraph from '@/components/NetworkGraph';
import { EmptyState } from '@/components/EmptyState';
import { ErrorState } from '@/components/ErrorState';
import { Network } from 'lucide-react';

export const revalidate = 10;
export const dynamic = 'force-dynamic';

export default async function GraphPage() {
  try {
    const data = await fetchGraphData(200);

    return (
      <div className="flex flex-col max-w-7xl mx-auto h-full">
        <div className="flex flex-col gap-2 mb-6">
          <h1 className="text-xl font-semibold text-text">Network Flow Graph</h1>
          <p className="text-sm text-text-muted">Visualize account interactions and identify clusters of high-risk activity.</p>
        </div>

        {data.nodes.length === 0 ? (
          <EmptyState 
            icon={Network}
            title="No network data"
            hint="Run the analyzers to generate transaction flows."
          />
        ) : (
          <NetworkGraph data={data} />
        )}
      </div>
    );
  } catch (error) {
    return (
      <div className="max-w-7xl mx-auto py-12">
        <ErrorState message="Failed to load graph data. The backend may be offline." />
      </div>
    );
  }
}
