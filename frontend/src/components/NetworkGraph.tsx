'use client';
import { useEffect, useRef, useState } from 'react';
import dynamic from 'next/dynamic';
import { severityConfig } from '@/lib/severity';
import { GraphData, GraphNode, GraphEdge } from '@/lib/api';

// Dynamically import ForceGraph2D since it uses canvas/window
const ForceGraph2D = dynamic(() => import('react-force-graph-2d'), {
  ssr: false,
  loading: () => <div className="w-full h-full flex items-center justify-center text-text-muted">Loading Graph Engine...</div>
});

interface Props {
  data: GraphData;
}

export default function NetworkGraph({ data }: Props) {
  const fgRef = useRef<any>(null);
  const [containerDimensions, setContainerDimensions] = useState({ width: 800, height: 600 });
  const containerRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (containerRef.current) {
      const { clientWidth, clientHeight } = containerRef.current;
      setContainerDimensions({ width: clientWidth, height: clientHeight });
    }
    
    const handleResize = () => {
      if (containerRef.current) {
        const { clientWidth, clientHeight } = containerRef.current;
        setContainerDimensions({ width: clientWidth, height: clientHeight });
      }
    };
    window.addEventListener('resize', handleResize);
    return () => window.removeEventListener('resize', handleResize);
  }, []);

  // Process data for graph
  const gData = {
    nodes: data.nodes.map(n => ({
      ...n,
      val: Math.max(2, n.score / 10), // Node size based on score
      color: severityConfig[n.risk_band.toLowerCase()]?.varSolid || 'var(--text-muted)'
    })),
    links: data.edges.map(e => ({
      ...e,
      source: e.source,
      target: e.target,
      value: Math.max(1, Math.log10(e.amount)) // Edge width based on log of amount
    }))
  };

  return (
    <div ref={containerRef} className="w-full h-[600px] bg-surface border border-border shadow-sm rounded-[var(--r-card)] overflow-hidden">
      {typeof window !== 'undefined' && (
        <ForceGraph2D
          ref={fgRef}
          width={containerDimensions.width}
          height={containerDimensions.height}
          graphData={gData}
          nodeLabel={(node: any) => `${node.id} | Score: ${node.score} | ${node.risk_band.toUpperCase()}`}
          nodeColor={(node: any) => node.color}
          nodeRelSize={4}
          linkColor={() => 'var(--border)'}
          linkWidth={(link: any) => link.value}
          linkDirectionalArrowLength={3.5}
          linkDirectionalArrowRelPos={1}
          onNodeClick={(node: any) => {
            // Optional: navigate to account detail page
            window.location.href = `/accounts/${node.id}`;
          }}
          backgroundColor="var(--bg)"
        />
      )}
    </div>
  );
}
