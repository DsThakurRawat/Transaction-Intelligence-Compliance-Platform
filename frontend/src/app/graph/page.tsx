import { fetchGraphData } from "@/lib/api";
import NetworkGraph from "@/components/NetworkGraph";
import { Suspense } from "react";

export const dynamic = 'force-dynamic';

async function GraphContainer() {
  try {
    const data = await fetchGraphData(100); // Top 100 risky accounts + their counterparties
    
    if (data.nodes.length === 0) {
      return (
        <div className="p-12 text-center border border-border bg-surface rounded-[var(--r-card)] text-text-muted">
          No graph data available. Run the data generator to inject anomalies.
        </div>
      );
    }
    
    return <NetworkGraph data={data} />;
  } catch (error) {
    return (
      <div className="p-6 bg-risk-critical-soft text-risk-critical rounded-[var(--r-card)] border border-risk-critical/20">
        Couldn&apos;t load network graph. Check if the API is running and Option A counterparty data exists.
      </div>
    );
  }
}

export default function GraphPage() {
  return (
    <div className="max-w-6xl mx-auto flex flex-col gap-6">
      <div className="flex justify-between items-end">
        <div>
          <h1 className="text-2xl font-semibold mb-2">Network Graph</h1>
          <p className="text-text-muted">Force-directed visualization of flagged money flows and laundering structures.</p>
        </div>
      </div>
      
      <Suspense fallback={<div className="animate-pulse bg-surface-2 h-[600px] rounded-[var(--r-card)]"></div>}>
        <GraphContainer />
      </Suspense>
    </div>
  );
}
